"""HP - Hesitation Pause (M+D): Mid-thought pause that signals uncertainty."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, PriorSignals
from utils.transcript import get_candidate_turns, count_fillers


def score_hp(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="HP", name="Hesitation Pause", category="Pauses & Silence",
                            layer="M+D", source="transcript", score=3, confidence=0.3,
                            raw={}, evidence=["No turns"])

    pauses = report.get("pauses", [])
    candidate_pauses = [p for p in pauses if p.get("speaker") == "SPEAKER_0"]

    hesitation_pauses = [p for p in candidate_pauses if 0.5 <= p["duration"] <= 2.0]
    hp_count = len(hesitation_pauses)
    total_words = sum(t["word_count"] for t in turns)
    total_fillers = sum(count_fillers(t["text"]) for t in turns)
    hp_with_fillers = sum(1 for p in hesitation_pauses
                          if any(count_fillers(t["text"]) > 0
                                 for t in turns
                                 if t["id"] == p.get("turn_id")))
    hesitation_ratio = hp_with_fillers / max(1, hp_count)
    rate_per_100 = (hp_count / max(1, total_words)) * 100

    if rate_per_100 > 5 or hesitation_ratio > 0.7:
        score = 0
    elif rate_per_100 > 3 or hesitation_ratio > 0.5:
        score = 1
    elif rate_per_100 > 1.5:
        score = 2
    elif rate_per_100 > 0.5:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="HP", name="Hesitation Pause", category="Pauses & Silence", layer="M+D",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"hp_count": hp_count, "hp_with_fillers": hp_with_fillers,
             "hesitation_ratio": round(hesitation_ratio, 3),
             "rate_per_100": round(rate_per_100, 2)},
        evidence=[f"HP count={hp_count}", f"Rate={rate_per_100:.1f}/100w"],
        depends_on=["FP"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python hp.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_hp(report)
    print(json.dumps(result.to_dict(), indent=2))
