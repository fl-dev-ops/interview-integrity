"""Rep - Repetition (M): Repeated words or phrases. Higher = less repetition."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns, count_adjacent_repeats, count_repeated_bigrams


def score_rep(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Rep", name="Repetition", category="Fluency",
                            layer="M", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_adj_repeats = 0
    total_bigram_repeats = 0
    total_words = 0

    for t in turns:
        total_adj_repeats += count_adjacent_repeats(t["text"])
        total_bigram_repeats += count_repeated_bigrams(t["text"])
        total_words += t["word_count"]

    total_repeats = total_adj_repeats + total_bigram_repeats
    rate_per_100 = (total_repeats / max(1, total_words)) * 100

    if rate_per_100 > 5:
        score = 0
    elif rate_per_100 > 3:
        score = 1
    elif rate_per_100 > 1.5:
        score = 2
    elif rate_per_100 > 0.5:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Rep", name="Repetition", category="Fluency", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.85,
        raw={"adj_repeats": total_adj_repeats, "bigram_repeats": total_bigram_repeats,
             "total_repeats": total_repeats, "total_words": total_words,
             "rate_per_100": round(rate_per_100, 2)},
        evidence=[f"Repeats={total_repeats}", f"Rate={rate_per_100:.1f}/100w"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rep.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_rep(report)
    print(json.dumps(result.to_dict(), indent=2))
