"""Ask - Clarifying (M+J): Appropriate clarifying questions when prompt is unclear."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_ask(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Ask", name="Clarifying", category="Conversation Behavior",
                            layer="M+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))

    prompt = f"""Rate the clarifying behavior of this interview candidate: appropriate clarifying questions when prompt is unclear.

Candidate answers:
{text}

Score on a 0-4 scale:
0: Does not clarify and answers wrong question
1: Rarely clarifies when needed
2: Clarification behavior is acceptable
3: Asks useful clarifying questions when appropriate
4: Clarifies strategically without overusing it

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
        code="Ask", name="Clarifying", category="Conversation Behavior", layer="M+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ask.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_ask(report)
    print(json.dumps(result.to_dict(), indent=2))
