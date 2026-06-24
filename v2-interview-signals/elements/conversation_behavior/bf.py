"""B&F - Back/Forth (J): Ability to sustain interview exchange."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns, get_interviewer_turns


def score_bf(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="B&F", name="Back/Forth", category="Conversation Behavior",
                            layer="J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    cand_turns = get_candidate_turns(report)
    int_turns = get_interviewer_turns(report)
    total_turns = len(cand_turns) + len(int_turns)
    cand_ratio = len(cand_turns) / max(1, total_turns)

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(cand_turns[:6]))
    stats = f"Candidate turns: {len(cand_turns)}, Interviewer turns: {len(int_turns)}, Ratio: {cand_ratio:.2f}"

    prompt = f"""Rate the back-and-forth ability of this interview candidate: ability to sustain interview exchange.

{stats}

Candidate answers:
{text}

Score on a 0-4 scale:
0: Cannot continue without heavy support
1: Needs frequent interviewer rescue
2: Manages basic exchange
3: Keeps conversation going with light support
4: Handles conversation and follow-ups naturally

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
        code="B&F", name="Back/Forth", category="Conversation Behavior", layer="J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"cand_ratio": round(cand_ratio, 3), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python bf.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_bf(report)
    print(json.dumps(result.to_dict(), indent=2))
