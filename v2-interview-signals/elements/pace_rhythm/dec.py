"""Dec - Deceleration (M): Decrease in WPM or momentum within an answer."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


def score_dec(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if len(turns) < 2:
        return SignalResult(code="Dec", name="Deceleration", category="Pace & Rhythm",
                            layer="M", source="transcript", score=3, confidence=0.3,
                            raw={"decel_rates": []}, evidence=["Too few turns"])

    wpm_list = []
    for t in turns:
        if t["duration"] > 0:
            wpm_list.append(t["word_count"] / (t["duration"] / 60))

    decel_rates = []
    for i in range(1, len(wpm_list)):
        if wpm_list[i - 1] > 0:
            decel_rates.append(wpm_list[i - 1] - wpm_list[i])

    if not decel_rates:
        avg_decel = 0.0
    else:
        avg_decel = sum(decel_rates) / len(decel_rates)

    max_decel = max(decel_rates) if decel_rates else 0

    if max_decel > 60 or avg_decel > 30:
        score = 0
    elif max_decel > 40 or avg_decel > 15:
        score = 1
    elif max_decel > 25 or avg_decel > 8:
        score = 2
    elif max_decel > 10:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Dec", name="Deceleration", category="Pace & Rhythm", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"avg_decel": round(avg_decel, 2), "max_decel": round(max_decel, 2),
             "decel_rates": [round(r, 2) for r in decel_rates]},
        evidence=[f"Avg decel={avg_decel:.1f} WPM", f"Max decel={max_decel:.1f} WPM"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python dec.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_dec(report)
    print(json.dumps(result.to_dict(), indent=2))
