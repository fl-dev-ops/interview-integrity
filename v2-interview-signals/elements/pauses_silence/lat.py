"""Lat - Latency (M): Time from interviewer question end to candidate answer start."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, pct
from utils.transcript import get_candidate_turns, get_interviewer_turns


def score_lat(report: dict) -> SignalResult:
    latencies = []
    turns = report.get("turns", [])

    for i, turn in enumerate(turns):
        if turn["speaker"] == "SPEAKER_0" and i > 0:
            prev = turns[i - 1]
            if prev["speaker"] == "SPEAKER_1":
                gap = turn["start"] - prev["end"]
                if -1.0 < gap < 30.0:
                    latencies.append(round(gap, 2))

    if not latencies:
        return SignalResult(code="Lat", name="Latency", category="Pauses & Silence",
                            layer="M", source="transcript", score=2, confidence=0.3,
                            raw={"latencies": []}, evidence=["No latency data"])

    avg_lat = sum(latencies) / len(latencies)
    p25 = pct(latencies, 25)
    p75 = pct(latencies, 75)

    too_fast = sum(1 for l in latencies if l < 1.0) / len(latencies)
    too_slow = sum(1 for l in latencies if l > 6.0) / len(latencies)

    if too_fast > 0.5 or too_slow > 0.5:
        score = 0
    elif too_fast > 0.3 or too_slow > 0.3:
        score = 1
    elif avg_lat < 2.0 or avg_lat > 5.0:
        score = 2
    elif 2.0 <= avg_lat <= 4.0:
        score = 4
    else:
        score = 3

    return SignalResult(
        code="Lat", name="Latency", category="Pauses & Silence", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.9,
        raw={"avg_latency": round(avg_lat, 2), "p25": round(p25, 2), "p75": round(p75, 2),
             "too_fast_ratio": round(too_fast, 3), "too_slow_ratio": round(too_slow, 3),
             "latencies": latencies},
        evidence=[f"Avg={avg_lat:.2f}s", f"Fast={too_fast:.0%}", f"Slow={too_slow:.0%}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python lat.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_lat(report)
    print(json.dumps(result.to_dict(), indent=2))
