"""Ton - Tone (J): Listener perception of voice quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call, llm_call_with_audio


def score_ton(report: dict, audio_path: Path | None = None, google_file: Any | None = None) -> SignalResult:
    turns = [t for t in report.get("turns", []) if t["speaker"] == "SPEAKER_0"]
    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:8]))

    prompt = f"""Listen to the candidate's voice audio and rate tone: listener perception of voice quality.

For context, the candidate said:
{text}

Score on a 0-4 scale based on what you HEAR in the voice:
0: Tone actively undermines the interview
1: Tone is inappropriate, very anxious, or robotic
2: Acceptable but inconsistent
3: Professional and mostly natural
4: Warm, composed, and aligned with the interview context

Categories: warm, nervous, flat, robotic, casual, confident, strained

Return JSON: {{"score": <0-4>, "tone_category": "<label>", "reasoning": "<brief>"}}"""

    system = "You are an interview audio analysis expert. Analyze the candidate's VOICE tone — warmth, nervousness, confidence, professionalism — based on how they sound, not what they say. Return JSON only."

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
        code="Ton", name="Tone", category="Voice Delivery", layer="J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ton.py <report.json> [audio_path]"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    audio = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = score_ton(report, audio)
    print(json.dumps(result.to_dict(), indent=2))
