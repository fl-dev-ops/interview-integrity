"""RepW - Word Repeat (M): Repeated lexical choices, excluding necessary terms."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns, tokenize_words


def score_repw(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="RepW", name="Word Repeat", category="Language Quality",
                            layer="M", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_repeat_words = 0
    total_words = 0

    for t in turns:
        words = tokenize_words(t["text"])
        total_words += len(words)
        if len(words) > 3:
            unique = set(words)
            repeat_count = len(words) - len(unique)
            total_repeat_words += repeat_count

    repeat_rate = (total_repeat_words / max(1, total_words)) * 100

    if repeat_rate > 20:
        score = 0
    elif repeat_rate > 12:
        score = 1
    elif repeat_rate > 6:
        score = 2
    elif repeat_rate > 2:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="RepW", name="Word Repeat", category="Language Quality", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.85,
        raw={"repeat_words": total_repeat_words, "total_words": total_words,
             "repeat_rate": round(repeat_rate, 2)},
        evidence=[f"Repeat words={total_repeat_words}", f"Rate={repeat_rate:.1f}%"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python repw.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_repw(report)
    print(json.dumps(result.to_dict(), indent=2))
