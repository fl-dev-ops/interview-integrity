#!/usr/bin/env python3
"""Identify speaker roles and canonicalize v2 reports.

v2 canonical IDs:
  - SPEAKER_1 = interviewer
  - SPEAKER_0 = candidate

Updates transcript.json and report.json in place.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))


DEFAULT_MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class SpeakerIdentification(BaseModel):
    interviewer_speaker_id: str = Field(description="Original interviewer speaker ID")
    candidate_speaker_id: str = Field(description="Original candidate speaker ID")
    confidence: float = Field(description="Confidence from 0 to 1")
    reasoning: str = Field(description="Brief explanation")


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_openrouter_client():
    from openai import OpenAI

    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def identify_speakers(turns: list[dict], model: str = DEFAULT_MODEL) -> dict:
    client = get_openrouter_client()
    speaker_turns: dict[str, list[dict]] = {}
    for turn in turns:
        speaker_turns.setdefault(turn["speaker"], [])
        if len(speaker_turns[turn["speaker"]]) < 5:
            speaker_turns[turn["speaker"]].append(turn)

    sample_lines = []
    for speaker in sorted(speaker_turns):
        sample_lines.append(f"\n--- {speaker} ---")
        for turn in speaker_turns[speaker]:
            sample_lines.append(f"[{turn.get('word_count', '?')} words] {turn['text'][:300]}")
    if len(turns) > 10:
        mid = len(turns) // 2
        sample_lines.append("\n--- Middle turns ---")
        for turn in turns[mid - 2: mid + 2]:
            sample_lines.append(f"{turn['speaker']} [{turn.get('word_count', '?')} words] {turn['text'][:300]}")

    schema = SpeakerIdentification.model_json_schema()
    schema["additionalProperties"] = False
    messages = [
        {
            "role": "system",
            "content": "You identify interviewer and candidate speakers in diagnostic interview transcripts. Return JSON only.",
        },
        {
            "role": "user",
            "content": """Identify the interviewer and candidate/student.

Interviewer asks questions, gives instructions, and guides the conversation.
Candidate answers questions, describes background, skills, and experience.

Transcript sample:
{sample}

Return JSON matching the schema.""".format(sample="\n".join(sample_lines)),
        },
    ]
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_schema", "json_schema": {"name": "SpeakerIdentification", "strict": True, "schema": schema}},
                temperature=0,
                extra_body={"provider": {"require_parameters": True}, "plugins": [{"id": "response-healing"}]},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty speaker-identification response")
            return SpeakerIdentification.model_validate_json(content).model_dump()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def build_mapping(interviewer_id: str, candidate_id: str) -> dict[str, str]:
    mapping = {interviewer_id: "SPEAKER_1", candidate_id: "SPEAKER_0"}
    for original, canonical in list(mapping.items()):
        if original.startswith("SPEAKER_"):
            mapping[original.replace("SPEAKER_", "")] = canonical
        else:
            mapping[f"SPEAKER_{original}"] = canonical
    return mapping


def remap_id(value: str, mapping: dict[str, str]) -> str:
    return mapping.get(value, value)


def resolve_extra_speaker(extra_speaker: str, turns: list[dict]) -> str:
    extra_turns = [t for t in turns if t["speaker"] == extra_speaker]
    if not extra_turns:
        return "SPEAKER_0"
    extra_mid = sum((t["start"] + t["end"]) / 2 for t in extra_turns) / len(extra_turns)
    canonical = {}
    for speaker in ("SPEAKER_1", "SPEAKER_0"):
        speaker_turns = [t for t in turns if t["speaker"] == speaker]
        if speaker_turns:
            canonical[speaker] = sum((t["start"] + t["end"]) / 2 for t in speaker_turns) / len(speaker_turns)
    return min(canonical, key=lambda speaker: abs(extra_mid - canonical[speaker])) if canonical else "SPEAKER_0"


def canonicalize_report(report: dict, interviewer_id: str, candidate_id: str) -> dict:
    mapping = build_mapping(interviewer_id, candidate_id)
    for item in report.get("turns", []):
        item["speaker"] = remap_id(item["speaker"], mapping)
    for item in report.get("segments", []):
        item["speaker"] = remap_id(item["speaker"], mapping)

    turns = report.get("turns", [])
    remaining = {t["speaker"] for t in turns} - {"SPEAKER_1", "SPEAKER_0"}
    extra_mapping = {speaker: resolve_extra_speaker(speaker, turns) for speaker in remaining}
    for item in turns:
        item["speaker"] = extra_mapping.get(item["speaker"], item["speaker"])
    for item in report.get("segments", []):
        item["speaker"] = extra_mapping.get(item["speaker"], item["speaker"])

    merged = []
    for turn in turns:
        if merged and merged[-1]["speaker"] == turn["speaker"]:
            merged[-1]["text"] += " " + turn["text"]
            merged[-1]["end"] = turn["end"]
            merged[-1]["duration"] = round(merged[-1]["end"] - merged[-1]["start"], 2)
            merged[-1]["word_count"] = len(merged[-1]["text"].split())
            merged[-1]["segment_ids"] = merged[-1].get("segment_ids", []) + turn.get("segment_ids", [])
        else:
            merged.append(turn)
    for index, turn in enumerate(merged, 1):
        turn["id"] = index
    report["turns"] = merged

    for item in report.get("latency", []):
        item["from_speaker"] = extra_mapping.get(remap_id(item["from_speaker"], mapping), remap_id(item["from_speaker"], mapping))
        item["to_speaker"] = extra_mapping.get(remap_id(item["to_speaker"], mapping), remap_id(item["to_speaker"], mapping))
    for item in report.get("pauses", []):
        item["speaker"] = extra_mapping.get(remap_id(item["speaker"], mapping), remap_id(item["speaker"], mapping))
    for item in report.get("overlaps", []):
        item["speaker_a"] = extra_mapping.get(remap_id(item["speaker_a"], mapping), remap_id(item["speaker_a"], mapping))
        item["speaker_b"] = extra_mapping.get(remap_id(item["speaker_b"], mapping), remap_id(item["speaker_b"], mapping))
    if "stats" in report:
        report["stats"] = {extra_mapping.get(remap_id(speaker, mapping), remap_id(speaker, mapping)): value for speaker, value in report["stats"].items()}
    report["speaker_roles"] = {"SPEAKER_1": "interviewer", "SPEAKER_0": "candidate"}
    return report


def canonicalize_transcript(transcript: dict, interviewer_id: str, candidate_id: str) -> dict:
    mapping = build_mapping(interviewer_id, candidate_id)
    for entry in transcript.get("diarized_transcript", {}).get("entries", []):
        entry["speaker_id"] = remap_id(str(entry["speaker_id"]), mapping)
    return transcript


def fix_session(session_dir: Path, model: str = DEFAULT_MODEL) -> dict:
    report_path = session_dir / "report.json"
    transcript_path = session_dir / "transcript.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    turns = report.get("turns", [])
    if not turns:
        raise ValueError(f"No turns in {report_path}")

    speakers = {turn["speaker"] for turn in turns}
    if speakers <= {"SPEAKER_1", "SPEAKER_0"} and report.get("speaker_roles"):
        return {"status": "already_fixed", "session_dir": str(session_dir)}

    result = identify_speakers(turns, model=model)
    report = canonicalize_report(report, result["interviewer_speaker_id"], result["candidate_speaker_id"])
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if transcript_path.exists():
        transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
        transcript = canonicalize_transcript(transcript, result["interviewer_speaker_id"], result["candidate_speaker_id"])
        transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "fixed", **result, "session_dir": str(session_dir)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix speaker roles in v2 transcript/report")
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    result = fix_session(args.session_dir, model=args.model)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
