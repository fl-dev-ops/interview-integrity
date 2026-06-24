"""Pac - Pace Control (D): Consistency and appropriateness of speaking speed."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, pct, PriorSignals
from utils.transcript import get_candidate_turns


def score_pac(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Pac", name="Pace Control", category="Pace & Rhythm",
                            layer="D", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    wpm_list = []
    for t in turns:
        if t["duration"] > 0:
            wpm_list.append(t["word_count"] / (t["duration"] / 60))

    avg_wpm = sum(wpm_list) / max(1, len(wpm_list))
    p25 = pct(wpm_list, 25)
    p75 = pct(wpm_list, 75)
    spread = p75 - p25
    out_of_range = sum(1 for w in wpm_list if w < 90 or w > 170) / max(1, len(wpm_list))

    if out_of_range > 0.5:
        score = 0
    elif out_of_range > 0.3 or spread > 60:
        score = 1
    elif out_of_range > 0.15 or spread > 40:
        score = 2
    elif out_of_range > 0.05 or spread > 25:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Pac", name="Pace Control", category="Pace & Rhythm", layer="D",
        source="transcript", score=clamp_score(score), confidence=0.8,
        raw={"avg_wpm": round(avg_wpm, 1), "spread": round(spread, 1),
             "out_of_range_ratio": round(out_of_range, 3)},
        evidence=[f"Avg WPM={avg_wpm:.1f}", f"Spread={spread:.1f}", f"Out-of-range={out_of_range:.1%}"],
        depends_on=["WPM", "Rus", "Drg"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pac.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_pac(report)
    print(json.dumps(result.to_dict(), indent=2))
