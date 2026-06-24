"""Coh - Cohesion (D+J): How well ideas connect across phrases/sentences."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, build_signal_context, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns, count_connectors


def score_coh(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Coh", name="Cohesion", category="Fluency",
                            layer="D+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_connectors = sum(count_connectors(t["text"]) for t in turns)
    total_words = sum(t["word_count"] for t in turns)
    connector_rate = (total_connectors / max(1, total_words)) * 100

    text = "\n".join(f"[{i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:6]))
    signal_ctx = build_signal_context(prior_signals, ["Conn"])

    prompt = f"""Rate the cohesion of this interview candidate: how well ideas connect across phrases/sentences.
{"Use both the transcript evidence and the pre-computed signal scores below." if signal_ctx else ""}

{signal_ctx}

Connector usage: {total_connectors} connectors in {total_words} words ({connector_rate:.1f}/100w)

Candidate answers:
{text}

Score on a 0-4 scale:
0: Disconnected words or fragments
1: Mostly list-like, weak connection
2: Basic sequence with some gaps
3: Clear flow between ideas
4: Smooth, structured, and purposeful flow

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
        code="Coh", name="Cohesion", category="Fluency", layer="D+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"connectors": total_connectors, "connector_rate": round(connector_rate, 2), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=["Conn"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python coh.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_coh(report)
    print(json.dumps(result.to_dict(), indent=2))
