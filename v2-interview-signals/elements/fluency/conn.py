"""Conn - Connector Words (M+J): Use of linking words beyond and, but, so."""

from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns, tokenize_words, CONNECTORS


BASIC_CONNECTORS = {"and", "but", "so", "then", "also", "or"}
ADVANCED_CONNECTORS = CONNECTORS - BASIC_CONNECTORS


def score_conn(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Conn", name="Connector Words", category="Fluency",
                            layer="M+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_basic = 0
    total_advanced = 0
    total_words = 0

    for t in turns:
        words = tokenize_words(t["text"])
        total_words += len(words)
        for w in words:
            if w in BASIC_CONNECTORS:
                total_basic += 1
            elif w in ADVANCED_CONNECTORS:
                total_advanced += 1

    total_connectors = total_basic + total_advanced
    advanced_ratio = total_advanced / max(1, total_connectors)

    if total_connectors == 0:
        score = 0
    elif advanced_ratio < 0.1:
        score = 1
    elif advanced_ratio < 0.3:
        score = 2
    elif advanced_ratio < 0.6:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Conn", name="Connector Words", category="Fluency", layer="M+J",
        source="transcript", score=clamp_score(score), confidence=0.8,
        raw={"basic_count": total_basic, "advanced_count": total_advanced,
             "total_connectors": total_connectors,
             "advanced_ratio": round(advanced_ratio, 3)},
        evidence=[f"Basic={total_basic}", f"Advanced={total_advanced}",
                   f"Adv ratio={advanced_ratio:.1%}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python conn.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_conn(report)
    print(json.dumps(result.to_dict(), indent=2))
