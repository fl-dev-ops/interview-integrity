"""Idi - Idioms (J): Natural idiomatic/colloquial phrasing appropriate to context."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_idi(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Idi", name="Idioms", category="Language Quality",
                            layer="J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    text = "\n".join(f"[{i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:8]))

    prompt = f"""Rate the idiomatic usage of this interview candidate: natural idiomatic/colloquial phrasing.

Candidate answers:
{text}

Score on a 0-4 scale:
0: Unnatural phrasing repeatedly confuses meaning
1: Very limited natural phrasing
2: Some natural phrases but inconsistent
3: Mostly natural, context-appropriate language
4: Idiomatic ease with professional control

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
        code="Idi", name="Idioms", category="Language Quality", layer="J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw=result, evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python idi.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_idi(report)
    print(json.dumps(result.to_dict(), indent=2))
