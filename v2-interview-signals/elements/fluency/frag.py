"""Frag - Fragments (M+D): Incomplete or broken phrases. Higher = fewer fragments."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


def _count_fragments(text: str) -> int:
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    fragments = 0
    for s in sentences:
        words = s.split()
        if len(words) < 4 and not any(w in s.lower() for w in ["yes", "no", "ok", "right"]):
            fragments += 1
    return fragments


def score_frag(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Frag", name="Fragments", category="Fluency",
                            layer="M+D", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_frag = 0
    total_words = 0
    for t in turns:
        total_frag += _count_fragments(t["text"])
        total_words += t["word_count"]

    rate_per_100 = (total_frag / max(1, total_words)) * 100

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
        code="Frag", name="Fragments", category="Fluency", layer="M+D",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"total_fragments": total_frag, "total_words": total_words,
             "rate_per_100": round(rate_per_100, 2)},
        evidence=[f"Fragments={total_frag}", f"Rate={rate_per_100:.1f}/100w"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python frag.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_frag(report)
    print(json.dumps(result.to_dict(), indent=2))
