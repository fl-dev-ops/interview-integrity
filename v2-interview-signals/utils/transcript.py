"""Transcript loading and turn extraction utilities."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


FILLER_RE = re.compile(r"\b(um+|uh+|erm+|hmm+|like|you know|basically|actually)\b", re.I)


def load_report(report_path: Path) -> dict:
    """Load report.json from disk."""
    return json.loads(report_path.read_text(encoding="utf-8"))


def load_transcript(transcript_path: Path) -> dict:
    """Load transcript.json from disk."""
    return json.loads(transcript_path.read_text(encoding="utf-8"))


def build_segments(entries: list[dict]) -> list[dict]:
    return [
        {
            "speaker": f"SPEAKER_{e['speaker_id']}" if not str(e["speaker_id"]).startswith("SPEAKER_") else str(e["speaker_id"]),
            "start": round(float(e["start_time_seconds"]), 2),
            "end": round(float(e["end_time_seconds"]), 2),
            "text": e.get("transcript", "").strip(),
        }
        for e in entries
        if e.get("transcript", "").strip()
    ]


def finalize_turn(raw: dict, turn_id: int) -> dict:
    text = " ".join(raw["texts"]).strip()
    duration = max(0.0, raw["end"] - raw["start"])
    return {
        "id": turn_id,
        "speaker": raw["speaker"],
        "start": raw["start"],
        "end": raw["end"],
        "segment_ids": raw["segment_ids"],
        "text": text,
        "word_count": len(text.split()),
        "duration": round(duration, 2),
    }


def build_turns(segments: list[dict]) -> list[dict]:
    if not segments:
        return []
    turns = []
    current = {
        "speaker": segments[0]["speaker"],
        "start": segments[0]["start"],
        "end": segments[0]["end"],
        "texts": [segments[0]["text"]],
        "segment_ids": [0],
    }
    for i, seg in enumerate(segments[1:], start=1):
        if seg["speaker"] == current["speaker"]:
            current["end"] = seg["end"]
            current["texts"].append(seg["text"])
            current["segment_ids"].append(i)
        else:
            turns.append(finalize_turn(current, len(turns) + 1))
            current = {
                "speaker": seg["speaker"],
                "start": seg["start"],
                "end": seg["end"],
                "texts": [seg["text"]],
                "segment_ids": [i],
            }
    turns.append(finalize_turn(current, len(turns) + 1))
    return turns


def build_latency(turns: list[dict]) -> list[dict]:
    out = []
    for prev, curr in zip(turns, turns[1:]):
        if prev["speaker"] != curr["speaker"]:
            out.append({
                "from_turn_id": prev["id"],
                "to_turn_id": curr["id"],
                "from_speaker": prev["speaker"],
                "to_speaker": curr["speaker"],
                "duration": round(curr["start"] - prev["end"], 2),
            })
    return out


def build_pauses(segments: list[dict], turns: list[dict]) -> list[dict]:
    pauses = []
    for turn in turns:
        for prev_id, curr_id in zip(turn["segment_ids"], turn["segment_ids"][1:]):
            gap = round(segments[curr_id]["start"] - segments[prev_id]["end"], 2)
            if gap > 0:
                pauses.append({
                    "turn_id": turn["id"],
                    "speaker": turn["speaker"],
                    "start": segments[prev_id]["end"],
                    "end": segments[curr_id]["start"],
                    "duration": gap,
                })
    return pauses


def build_overlaps(segments: list[dict]) -> list[dict]:
    overlaps = []
    for i, a in enumerate(segments):
        for j in range(i + 1, len(segments)):
            b = segments[j]
            if b["start"] >= a["end"]:
                break
            if a["speaker"] == b["speaker"]:
                continue
            start, end = max(a["start"], b["start"]), min(a["end"], b["end"])
            if end > start:
                overlaps.append({
                    "segment_a": i,
                    "segment_b": j,
                    "speaker_a": a["speaker"],
                    "speaker_b": b["speaker"],
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "duration": round(end - start, 2),
                })
    return overlaps


def infer_interviewer_speaker(report: dict) -> str:
    """Infer interviewer speaker ID from a normalized report."""
    turns = report.get("turns", [])
    speakers = {t.get("speaker") for t in turns}
    if "SPEAKER_00" in speakers:
        return "SPEAKER_00"
    if turns:
        return turns[0]["speaker"]
    return "SPEAKER_1"


def infer_candidate_speaker(report: dict) -> str:
    """Infer candidate speaker ID from a normalized report."""
    turns = report.get("turns", [])
    speakers = {t.get("speaker") for t in turns}
    if "SPEAKER_01" in speakers:
        return "SPEAKER_01"
    interviewer = infer_interviewer_speaker(report)
    speaking_time: dict[str, float] = {}
    for turn in turns:
        speaker = turn.get("speaker")
        if not speaker or speaker == interviewer:
            continue
        speaking_time[speaker] = speaking_time.get(speaker, 0.0) + float(turn.get("duration", 0.0))
    if speaking_time:
        return max(speaking_time, key=speaking_time.get)
    return "SPEAKER_0"


def get_candidate_turns(report: dict, candidate: str | None = None) -> list[dict]:
    candidate = candidate or infer_candidate_speaker(report)
    return [t for t in report["turns"] if t["speaker"] == candidate]


def get_interviewer_turns(report: dict, interviewer: str | None = None) -> list[dict]:
    interviewer = interviewer or infer_interviewer_speaker(report)
    return [t for t in report["turns"] if t["speaker"] == interviewer]


def build_qa_pairs(report: dict, interviewer: str | None = None, candidate: str | None = None) -> list[dict]:
    interviewer = interviewer or infer_interviewer_speaker(report)
    candidate = candidate or infer_candidate_speaker(report)
    pairs = []
    turns = report["turns"]
    for i, turn in enumerate(turns):
        if turn["speaker"] != candidate:
            continue
        question = None
        for prev in reversed(turns[:i]):
            if prev["speaker"] == interviewer:
                question = prev
                break
        pairs.append({
            "question_turn_id": question["id"] if question else None,
            "answer_turn_id": turn["id"],
            "question": question["text"] if question else "",
            "answer": turn["text"],
            "answer_start": turn["start"],
            "answer_end": turn["end"],
            "duration": turn["duration"],
            "word_count": turn["word_count"],
        })
    return pairs


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text.lower())


def count_fillers(text: str) -> int:
    return len(FILLER_RE.findall(text))


def count_adjacent_repeats(text: str) -> int:
    words = tokenize_words(text)
    return sum(1 for a, b in zip(words, words[1:]) if a == b)


def count_repeated_bigrams(text: str) -> int:
    words = tokenize_words(text)
    bigrams = list(zip(words, words[1:]))
    return sum(1 for a, b in zip(bigrams, bigrams[1:]) if a == b)


CONNECTORS = {"however", "therefore", "although", "despite", "because", "since", "while", "whereas", "moreover", "furthermore", "instead", "as", "result", "first", "second", "finally"}


def count_connectors(text: str) -> int:
    words = tokenize_words(text)
    return sum(1 for w in words if w in CONNECTORS)
