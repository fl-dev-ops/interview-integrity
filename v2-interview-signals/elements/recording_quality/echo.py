"""Echo - Echo (M): Room echo/reverb or call echo. Higher = less harmful echo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call, llm_call_with_audio


def score_echo(report: dict, audio_path: Path | None = None, google_file: Any | None = None) -> SignalResult:
    turns = [t for t in report.get("turns", []) if t["speaker"] == "SPEAKER_0"]
    if not turns:
        return SignalResult(code="Echo", name="Echo", category="Recording Quality",
                            layer="M", source="audio", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    prompt = """Listen to this audio recording and rate the echo/reverb level (higher = less harmful echo).

Score on a 0-4 scale:
0: Echo makes evaluation difficult
1: Strong echo distracts often
2: Noticeable echo but usable
3: Minor echo
4: Clean, dry enough recording

Return JSON: {"score": <0-4>, "reasoning": "<brief>"}"""

    system = "You are an audio quality analysis expert. Focus on room echo, reverb, and acoustic reflections. Return JSON only."

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
        code="Echo", name="Echo", category="Recording Quality", layer="M",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python echo.py <report.json> [audio_path]"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    audio = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = score_echo(report, audio)
    print(json.dumps(result.to_dict(), indent=2))
