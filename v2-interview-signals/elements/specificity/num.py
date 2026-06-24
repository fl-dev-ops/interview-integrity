"""Num - Numbers (M+J): Meaningful numbers, dates, amounts, metrics, counts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


NUMBER_RE = re.compile(r"\b\d[\d,]*\.?\d*\b")


def score_num(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Num", name="Numbers", category="Specificity",
                            layer="M+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_numbers = 0
    for t in turns:
        total_numbers += len(NUMBER_RE.findall(t["text"]))

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))

    prompt = f"""Rate the number usage of this interview candidate: meaningful numbers, dates, amounts, metrics, counts.

Numbers found in text: {total_numbers}

Candidate answers:
{text}

Score on a 0-4 scale:
0: No numbers where useful
1: Vague quantities only
2: Some numbers but limited value
3: Useful specific numbers
4: Exact, relevant, and impact-bearing numbers

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
        code="Num", name="Numbers", category="Specificity", layer="M+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"total_numbers": total_numbers, **result},
        evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python num.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_num(report)
    print(json.dumps(result.to_dict(), indent=2))
