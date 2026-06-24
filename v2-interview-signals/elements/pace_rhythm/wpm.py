"""WPM - Words Per Minute (M): Spoken words divided by speaking time."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, band_score
from utils.transcript import get_candidate_turns


def score_wpm(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="WPM", name="Words Per Minute", category="Pace & Rhythm",
                            layer="M", source="transcript", score=0, confidence=0.5,
                            raw={"turn_wpm": []}, evidence=["No candidate turns"])

    turn_wpm = []
    for t in turns:
        dur = t["duration"]
        if dur > 0:
            wpm = t["word_count"] / (dur / 60)
            turn_wpm.append(round(wpm, 1))

    if not turn_wpm:
        avg_wpm = 0.0
    else:
        avg_wpm = sum(turn_wpm) / len(turn_wpm)

    score = band_score(avg_wpm, [
        (70, 0), (90, 1), (100, 2), (120, 3), (145, 4), (160, 3), (180, 2), (210, 1), (999, 0)
    ])

    return SignalResult(
        code="WPM", name="Words Per Minute", category="Pace & Rhythm", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.9,
        raw={"avg_wpm": round(avg_wpm, 1), "turn_wpm": turn_wpm, "turn_count": len(turns)},
        evidence=[f"Avg WPM={avg_wpm:.1f}", f"Turns={len(turns)}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python wpm.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_wpm(report)
    print(json.dumps(result.to_dict(), indent=2))
