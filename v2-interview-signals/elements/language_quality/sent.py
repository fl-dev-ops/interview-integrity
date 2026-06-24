"""Sent - Sentence (D+J): Sentence completeness, order, and complexity."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, build_signal_context, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_sent(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Sent", name="Sentence", category="Language Quality",
                            layer="D+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[{i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:8]))
    signal_ctx = build_signal_context(prior_signals, ["Grm"])

    prompt = f"""Rate the sentence quality of this interview candidate: completeness, order, and complexity.
{"Use both the transcript evidence and the pre-computed signal scores below." if signal_ctx else ""}

{signal_ctx}

Candidate answers:
{text}

Score on a 0-4 scale:
0: Mostly incomplete phrases
1: Frequent broken or incorrect sentences
2: Simple sentences mostly understandable
3: Mostly complete with some complexity
4: Complete, varied, and controlled structures

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
        code="Sent", name="Sentence", category="Language Quality", layer="D+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=["Grm"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sent.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_sent(report)
    print(json.dumps(result.to_dict(), indent=2))
