"""Voc - Vocabulary (D+J): Breadth, precision, and level of word choice."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns, tokenize_words


def score_voc(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Voc", name="Vocabulary", category="Language Quality",
                            layer="D+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    all_words = []
    for t in turns:
        all_words.extend(tokenize_words(t["text"]))

    unique_ratio = len(set(all_words)) / max(1, len(all_words))
    total_words = len(all_words)

    text = "\n".join(f"[{i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:8]))
    prompt = f"""Rate the vocabulary of this interview candidate: breadth, precision, and level of word choice.

Word stats: {total_words} total words, {len(set(all_words))} unique words, unique ratio={unique_ratio:.2f}

Candidate answers:
{text}

Score on a 0-4 scale:
0: Isolated/basic words only
1: Very limited range; repeated basic words
2: Sufficient but simple range
3: Varied and appropriate vocabulary
4: Broad, precise, and flexible vocabulary

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
        code="Voc", name="Vocabulary", category="Language Quality", layer="D+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"unique_ratio": round(unique_ratio, 3), "total_words": total_words, **result},
        evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python voc.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_voc(report)
    print(json.dumps(result.to_dict(), indent=2))
