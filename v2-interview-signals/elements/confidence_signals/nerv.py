"""Nerv - Nervousness (D+J): Audible anxiety or nervous behaviors. Higher = less harmful nervousness."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, PriorSignals
from utils.llm import llm_call
from utils.transcript import get_candidate_turns, count_fillers


def score_nerv(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Nerv", name="Nervousness", category="Confidence Signals",
                            layer="D+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    total_fillers = sum(count_fillers(t["text"]) for t in turns)
    total_words = sum(t["word_count"] for t in turns)
    filler_rate = (total_fillers / max(1, total_words)) * 100

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))
    stats = f"Filler rate: {filler_rate:.1f}/100w, Total fillers: {total_fillers}"

    prompt = f"""Rate the nervousness of this interview candidate: audible anxiety or nervous behaviors (higher = less harmful nervousness).

{stats}

Candidate answers:
{text}

Score on a 0-4 scale:
0: Nervousness dominates the interview
1: Frequent nervous signals
2: Noticeable but manageable nervousness
3: Minor nervousness
4: Calm or nerves are well controlled

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
        code="Nerv", name="Nervousness", category="Confidence Signals", layer="D+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"fillers": total_fillers, "filler_rate": round(filler_rate, 2), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=["FP", "HP"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python nerv.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_nerv(report)
    print(json.dumps(result.to_dict(), indent=2))
