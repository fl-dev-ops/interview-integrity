"""Turn - Turn-Taking (M+J): Interruptions, over-talking, or awkward turn timing."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.llm import llm_call
from utils.transcript import get_candidate_turns


def score_turn(report: dict) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Turn", name="Turn-Taking", category="Conversation Behavior",
                            layer="M+J", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    overlaps = report.get("overlaps", [])
    candidate_overlaps = [o for o in overlaps if "SPEAKER_0" in (o.get("speaker_a", ""), o.get("speaker_b", ""))]
    overlap_duration = sum(o["duration"] for o in candidate_overlaps)

    text = "\n".join(f"[Answer {i+1}] {t['text'][:500]}" for i, t in enumerate(turns[:6]))
    stats = f"Overlapping segments: {len(candidate_overlaps)}, Overlap duration: {overlap_duration:.1f}s"

    prompt = f"""Rate the turn-taking of this interview candidate: interruptions, over-talking, or awkward turn timing.

{stats}

Candidate answers:
{text}

Score on a 0-4 scale:
0: Turn-taking repeatedly disrupts interview
1: Frequent interruptions/overlap
2: Some awkward timing
3: Mostly clean turn-taking
4: Smooth, respectful turn-taking

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
        code="Turn", name="Turn-Taking", category="Conversation Behavior", layer="M+J",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"overlap_count": len(candidate_overlaps), "overlap_duration": round(overlap_duration, 2), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python turn.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_turn(report)
    print(json.dumps(result.to_dict(), indent=2))
