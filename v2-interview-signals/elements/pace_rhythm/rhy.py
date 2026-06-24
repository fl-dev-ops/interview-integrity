"""Rhy - Rhythm (D): Timing pattern across words, phrases, and pauses."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, pct, PriorSignals
from utils.transcript import get_candidate_turns


def score_rhy(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Rhy", name="Rhythm", category="Pace & Rhythm",
                            layer="D", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    wpm_list = []
    for t in turns:
        if t["duration"] > 0:
            wpm_list.append(t["word_count"] / (t["duration"] / 60))

    p25 = pct(wpm_list, 25)
    p75 = pct(wpm_list, 75)
    spread = p75 - p25
    avg_wpm = sum(wpm_list) / max(1, len(wpm_list))

    pauses = report.get("pauses", [])
    candidate_pauses = [p for p in pauses if p.get("speaker") == "SPEAKER_0"]
    pause_count = len(candidate_pauses)
    long_pauses = sum(1 for p in candidate_pauses if p["duration"] > 2.0)

    if spread > 80 and long_pauses > 3:
        score = 0
    elif spread > 60 or long_pauses > 5:
        score = 1
    elif spread > 40 or long_pauses > 2:
        score = 2
    elif spread > 25:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Rhy", name="Rhythm", category="Pace & Rhythm", layer="D",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"spread": round(spread, 1), "long_pauses": long_pauses, "pause_count": pause_count},
        evidence=[f"Spread={spread:.1f}", f"Long pauses={long_pauses}"],
        depends_on=["Pac"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rhy.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_rhy(report)
    print(json.dumps(result.to_dict(), indent=2))
