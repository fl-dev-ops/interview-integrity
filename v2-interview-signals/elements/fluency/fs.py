"""FS - False Starts (M): Stopped/restarted phrases. Higher = fewer false starts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


def _count_false_starts(text: str) -> int:
    words = text.split()
    count = 0
    i = 0
    while i < len(words):
        if i > 0 and len(words[i]) > 2:
            prev = words[i - 1][:3]
            curr = words[i][:3]
            if prev == curr:
                count += 1
        i += 1
    return count


def score_fs(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="FS", name="False Starts", category="Fluency",
                            layer="M", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_fs = 0
    total_words = 0
    per_turn = []

    for t in turns:
        fs = _count_false_starts(t["text"])
        total_fs += fs
        total_words += t["word_count"]
        per_turn.append({"turn_id": t["id"], "false_starts": fs, "words": t["word_count"]})

    rate_per_100 = (total_fs / max(1, total_words)) * 100

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
        code="FS", name="False Starts", category="Fluency", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.8,
        raw={"total_fs": total_fs, "total_words": total_words,
             "rate_per_100": round(rate_per_100, 2), "per_turn": per_turn},
        evidence=[f"FS={total_fs}", f"Rate={rate_per_100:.1f}/100w"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fs.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_fs(report)
    print(json.dumps(result.to_dict(), indent=2))
