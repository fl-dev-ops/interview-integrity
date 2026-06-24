"""Acc - Acceleration (M): Increase in WPM within an answer or under pressure."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


def score_acc(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if len(turns) < 2:
        return SignalResult(code="Acc", name="Acceleration", category="Pace & Rhythm",
                            layer="M", source="transcript", score=3, confidence=0.3,
                            raw={"acceleration_rates": []}, evidence=["Too few turns"])

    wpm_list = []
    for t in turns:
        if t["duration"] > 0:
            wpm_list.append(t["word_count"] / (t["duration"] / 60))

    accel_rates = []
    for i in range(1, len(wpm_list)):
        if wpm_list[i - 1] > 0:
            accel_rates.append(wpm_list[i] - wpm_list[i - 1])

    if not accel_rates:
        avg_accel = 0.0
    else:
        avg_accel = sum(accel_rates) / len(accel_rates)

    max_accel = max(accel_rates) if accel_rates else 0

    if max_accel > 60 or avg_accel > 30:
        score = 0
    elif max_accel > 40 or avg_accel > 15:
        score = 1
    elif max_accel > 25 or avg_accel > 8:
        score = 2
    elif max_accel > 10:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Acc", name="Acceleration", category="Pace & Rhythm", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"avg_accel": round(avg_accel, 2), "max_accel": round(max_accel, 2),
             "accel_rates": [round(r, 2) for r in accel_rates]},
        evidence=[f"Avg accel={avg_accel:.1f} WPM", f"Max accel={max_accel:.1f} WPM"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python acc.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_acc(report)
    print(json.dumps(result.to_dict(), indent=2))
