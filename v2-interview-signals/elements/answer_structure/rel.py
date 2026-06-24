"""Rel - Relevance (J): Fit between answer and question asked."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import build_qa_pairs


def score_rel(report: dict) -> SignalResult:
    qa_pairs = build_qa_pairs(report)
    if not qa_pairs:
        return SignalResult(code="Rel", name="Relevance", category="Answer Structure",
                            layer="J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No QA pairs"])

    text = "\n".join(
        f"[Q{i+1}] {q['question'][:200]}\n[A{i+1}] {q['answer'][:400]}"
        for i, q in enumerate(qa_pairs[:6])
    )

    prompt = f"""Rate the relevance of this interview candidate's answers: fit between answer and question asked.

QA pairs:
{text}

Score on a 0-4 scale:
0: Could answer any question
1: Loosely related but misses the ask
2: Addresses the question basically
3: Directly answers with a relevant example
4: Answers and connects to a broader principle

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
        code="Rel", name="Relevance", category="Answer Structure", layer="J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"qa_count": len(qa_pairs), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rel.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_rel(report)
    print(json.dumps(result.to_dict(), indent=2))
