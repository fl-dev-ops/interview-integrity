"""Recv - Recovery Speed (D): Time/quality of regaining control after disruption."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, build_signal_context, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_recv(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Recv", name="Recovery Speed", category="Confidence Signals",
                            layer="D", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))
    signal_ctx = build_signal_context(prior_signals, ["RP", "SC"])

    prompt = f"""Rate the recovery speed of this interview candidate: time/quality of regaining control after disruption.
{"Use both the transcript evidence and the pre-computed signal scores below." if signal_ctx else ""}

{signal_ctx}

Candidate answers:
{text}

Score on a 0-4 scale:
0: No recovery
1: Slow recovery, answer remains weak
2: Recovery after visible struggle
3: Quick recovery
4: Immediate recovery with no listener concern

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
        code="Recv", name="Recovery Speed", category="Confidence Signals", layer="D",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=["RP", "SC"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python recv.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_recv(report)
    print(json.dumps(result.to_dict(), indent=2))
