"""FP - Filled Pause (M): Filler tokens such as um, uh, like, you know."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns, count_fillers


def score_fp(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="FP", name="Filled Pause", category="Pauses & Silence",
                            layer="M", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_fillers = 0
    total_words = 0
    per_turn = []

    for t in turns:
        fc = count_fillers(t["text"])
        wc = t["word_count"]
        total_fillers += fc
        total_words += wc
        per_turn.append({"turn_id": t["id"], "fillers": fc, "words": wc})

    rate_per_100 = (total_fillers / max(1, total_words)) * 100

    if rate_per_100 > 10:
        score = 0
    elif rate_per_100 > 6:
        score = 1
    elif rate_per_100 > 3:
        score = 2
    elif rate_per_100 > 1:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="FP", name="Filled Pause", category="Pauses & Silence", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.9,
        raw={"total_fillers": total_fillers, "total_words": total_words,
             "rate_per_100": round(rate_per_100, 2), "per_turn": per_turn},
        evidence=[f"Fillers={total_fillers}", f"Rate={rate_per_100:.1f}/100w"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fp.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_fp(report)
    print(json.dumps(result.to_dict(), indent=2))
