"""Str - Structure (D+J): Answer organization."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, build_signal_context, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_str(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Str", name="Structure", category="Answer Structure",
                            layer="D+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))
    signal_ctx = build_signal_context(prior_signals, ["Ctx", "Act", "Res"])

    prompt = f"""Rate the structure of this interview candidate's answers: answer organization.
{"Use both the transcript evidence and the pre-computed signal scores below." if signal_ctx else ""}

{signal_ctx}

Candidate answers:
{text}

Scoring guidelines:
- Your score should be CONSISTENT with the signal scores above (if provided).
- Use the transcript to confirm or contextualize the signals, not to contradict them.

Score on a 0-4 scale:
0: No clear structure
1: Scattered or list-like
2: Basic order but incomplete
3: Clear beginning/middle/end
4: Purposeful structure that builds a strong answer

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
        code="Str", name="Structure", category="Answer Structure", layer="D+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=["Ctx", "Act", "Res"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python str.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_str(report)
    print(json.dumps(result.to_dict(), indent=2))
