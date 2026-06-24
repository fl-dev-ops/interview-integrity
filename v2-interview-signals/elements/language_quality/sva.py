"""SVA - Agreement (M+J): Subject-verb agreement errors."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_sva(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="SVA", name="Agreement", category="Language Quality",
                            layer="M+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[{i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:8]))

    prompt = f"""Rate the subject-verb agreement of this interview candidate (higher = better).

Candidate answers:
{text}

Score on a 0-4 scale:
0: Agreement errors repeatedly block meaning
1: Frequent agreement errors
2: Some errors, mostly understandable
3: Mostly correct agreement
4: Consistently correct agreement

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
        code="SVA", name="Agreement", category="Language Quality", layer="M+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sva.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_sva(report)
    print(json.dumps(result.to_dict(), indent=2))
