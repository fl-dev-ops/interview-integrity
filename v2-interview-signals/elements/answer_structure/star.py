"""STAR - STAR (C): Completeness of Situation, Task, Action, Result."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, build_signal_context, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_star(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="STAR", name="STAR", category="Answer Structure",
                            layer="C", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))
    signal_ctx = build_signal_context(prior_signals, ["Ctx", "Act", "Res", "Str"])

    prompt = f"""Rate the STAR framework completeness of this interview candidate: Situation, Task, Action, Result.
{"Use both the transcript evidence and the pre-computed signal scores below." if signal_ctx else ""}

{signal_ctx}

Candidate answers:
{text}

Scoring guidelines:
- Your score should be CONSISTENT with the signal scores above (if provided).
- Use the transcript to confirm or contextualize the signals, not to contradict them.

Score on a 0-4 scale:
0: No STAR components clear
1: Only situation or general claim present
2: Situation and action present, weak result
3: Clear situation/action/result
4: Complete STAR with insight or impact

Return JSON: {{"score": <0-4>, "components": {{"situation": <bool>, "task": <bool>, "action": <bool>, "result": <bool>}}, "reasoning": "<brief>"}}"""

    raw = llm_call(prompt, system="You are an interview analysis expert. Return JSON only.")
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    result = json.loads(raw)

    return SignalResult(
        code="STAR", name="STAR", category="Answer Structure", layer="C",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=["Ctx", "Act", "Res", "Str"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python star.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_star(report)
    print(json.dumps(result.to_dict(), indent=2))
