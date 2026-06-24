"""Flo - Speech Flow (D): Smoothness of spoken output."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns, count_fillers, count_adjacent_repeats


def score_flo(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Flo", name="Speech Flow", category="Fluency",
                            layer="D", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_fillers = sum(count_fillers(t["text"]) for t in turns)
    total_repeats = sum(count_adjacent_repeats(t["text"]) for t in turns)
    total_words = sum(t["word_count"] for t in turns)
    disruption_rate = ((total_fillers + total_repeats) / max(1, total_words)) * 100

    text = "\n".join(f"[{i+1}] {t['text'][:300]}" for i, t in enumerate(turns[:6]))
    prompt = f"""Rate the speech flow of this interview candidate: smoothness of spoken output.

Disruption metrics: fillers={total_fillers}, adjacent_repeats={total_repeats}, disruption_rate={disruption_rate:.1f}/100w

Candidate answers:
{text}

Score on a 0-4 scale:
0: Speech repeatedly breaks down
1: Frequent stops/restarts
2: Uneven but understandable
3: Mostly smooth with minor disruption
4: Effortless or intentionally paced flow

Return JSON: {{"score": <0-4>, "reasoning": "<brief>"}}"""

    raw = llm_call(prompt, system="You are an interview analysis expert. Return JSON only.")
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    result = json.loads(raw)

    return SignalResult(
        code="Flo", name="Speech Flow", category="Fluency", layer="D",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"fillers": total_fillers, "repeats": total_repeats,
             "disruption_rate": round(disruption_rate, 2), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=["FS", "Rep", "SC"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python flo.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_flo(report)
    print(json.dumps(result.to_dict(), indent=2))
