"""RP - Recovery Pause (D): Pause followed by a clearer or better answer."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, PriorSignals
from utils.transcript import get_candidate_turns
from utils.llm import llm_call


def score_rp(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="RP", name="Recovery Pause", category="Pauses & Silence",
                            layer="D", source="transcript", score=2, confidence=0.3,
                            raw={}, evidence=["No turns"])

    pauses = report.get("pauses", [])
    candidate_pauses = [p for p in pauses if p.get("speaker") == "SPEAKER_0"]
    recovery_pauses = [p for p in candidate_pauses if p["duration"] >= 0.8]

    text = "\n".join(f"[Answer {i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:6]))
    pause_summary = f"Total candidate pauses: {len(candidate_pauses)}, Recovery-length pauses (0.8s+): {len(recovery_pauses)}"

    prompt = f"""Rate the recovery pause quality of this interview candidate: whether pauses help or hurt communication.

{pause_summary}

Candidate answers:
{text}

Score on a 0-4 scale:
0: Pauses lead to breakdown
1: Recovery is rare or weak
2: Sometimes recovers after pausing
3: Usually resumes clearly after pauses
4: Pauses reliably improve answer quality

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
        code="RP", name="Recovery Pause", category="Pauses & Silence", layer="D",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"recovery_pause_count": len(recovery_pauses), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=["OP"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python rp.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_rp(report)
    print(json.dumps(result.to_dict(), indent=2))
