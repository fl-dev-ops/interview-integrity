"""SC - Self-Correct (M+D): Explicit corrections mid-sentence."""

from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


CORRECTION_PATTERNS = [
    re.compile(r"\b(I mean|sorry|rather|I meant|not X but|I mean to say)\b", re.I),
    re.compile(r"\b(or|I mean)\s+\w+", re.I),
]


def _count_self_corrections(text: str) -> int:
    count = 0
    for pattern in CORRECTION_PATTERNS:
        count += len(pattern.findall(text))
    return count


def score_sc(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="SC", name="Self-Correct", category="Fluency",
                            layer="M+D", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_sc = 0
    total_words = 0
    per_turn = []

    for t in turns:
        sc = _count_self_corrections(t["text"])
        total_sc += sc
        total_words += t["word_count"]
        per_turn.append({"turn_id": t["id"], "corrections": sc, "words": t["word_count"]})

    rate_per_100 = (total_sc / max(1, total_words)) * 100

    if rate_per_100 > 4:
        score = 0
    elif rate_per_100 > 2.5:
        score = 1
    elif rate_per_100 > 1:
        score = 2
    elif rate_per_100 > 0.3:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="SC", name="Self-Correct", category="Fluency", layer="M+D",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"total_sc": total_sc, "total_words": total_words,
             "rate_per_100": round(rate_per_100, 2), "per_turn": per_turn},
        evidence=[f"Corrections={total_sc}", f"Rate={rate_per_100:.1f}/100w"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sc.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_sc(report)
    print(json.dumps(result.to_dict(), indent=2))
