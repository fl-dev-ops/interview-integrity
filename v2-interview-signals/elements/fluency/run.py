"""Run - Run-On Speech (D): Speech without clean sentence/idea boundaries. Higher = fewer run-ons."""

from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


SENTENCE_END = re.compile(r"[.!?;:]+")


def score_run(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Run", name="Run-On Speech", category="Fluency",
                            layer="D", source="transcript", score=4, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_turns = len(turns)
    run_on_turns = 0

    for t in turns:
        text = t["text"].strip()
        sentences = [s.strip() for s in SENTENCE_END.split(text) if s.strip()]
        if len(sentences) <= 1 and t["word_count"] > 25:
            run_on_turns += 1

    run_on_ratio = run_on_turns / max(1, total_turns)

    if run_on_ratio > 0.6:
        score = 0
    elif run_on_ratio > 0.4:
        score = 1
    elif run_on_ratio > 0.2:
        score = 2
    elif run_on_ratio > 0.05:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Run", name="Run-On Speech", category="Fluency", layer="D",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"run_on_turns": run_on_turns, "run_on_ratio": round(run_on_ratio, 3)},
        evidence=[f"Run-on turns={run_on_turns}", f"Ratio={run_on_ratio:.1%}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_run(report)
    print(json.dumps(result.to_dict(), indent=2))
