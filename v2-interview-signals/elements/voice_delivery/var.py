"""Var - Vocal Variety (D): Pitch/tone variation across answers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call, llm_call_with_audio


def score_var(report: dict, audio_path: Path | None = None, google_file: Any | None = None) -> SignalResult:
    turns = [t for t in report.get("turns", []) if t["speaker"] == "SPEAKER_0"]
    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:8]))

    prompt = f"""Listen to the candidate's voice audio and rate vocal variety: pitch/tone variation across answers.

For context, the candidate said:
{text}

Score on a 0-4 scale based on what you HEAR in the voice:
0: Flat or erratic enough to hurt comprehension
1: Mostly flat; little expressive variation
2: Some variation, but inconsistent or unnatural
3: Natural variation in most answers
4: Deliberate variation that supports meaning and emphasis

Return JSON: {{"score": <0-4>, "reasoning": "<brief>"}}"""

    system = "You are an interview audio analysis expert. Analyze the candidate's VOICE qualities — pitch, intonation, expressiveness — not their word choice. Return JSON only."

    if google_file or audio_path:
        raw = llm_call_with_audio(audio_path or Path(), prompt, system=system, uploaded_file=google_file)
    else:
        raw = llm_call(prompt, system=system)

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    result = json.loads(raw)

    return SignalResult(
        code="Var", name="Vocal Variety", category="Voice Delivery", layer="D",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python var.py <report.json> [audio_path]"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    audio = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = score_var(report, audio)
    print(json.dumps(result.to_dict(), indent=2))
