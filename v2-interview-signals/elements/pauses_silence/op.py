"""OP - Owned Pause (D): Intentional, controlled thinking pauses."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, PriorSignals
from utils.transcript import get_candidate_turns, count_fillers


def score_op(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    pauses = report.get("pauses", [])
    candidate_pauses = [p for p in pauses if p.get("speaker") == "SPEAKER_0"]

    if not candidate_pauses:
        return SignalResult(code="OP", name="Owned Pause", category="Pauses & Silence",
                            layer="D", source="transcript", score=2, confidence=0.3,
                            raw={}, evidence=["No candidate pauses"])

    turns = get_candidate_turns(report)
    turn_map = {t["id"]: t for t in turns}

    owned_count = 0
    total_controlled = 0
    for p in candidate_pauses:
        duration = p["duration"]
        turn = turn_map.get(p.get("turn_id"), {})
        text = turn.get("text", "")
        has_filler = count_fillers(text) > 0
        is_mid = duration >= 0.8
        if is_mid and not has_filler:
            owned_count += 1
        if duration >= 0.5:
            total_controlled += 1

    owned_ratio = owned_count / max(1, len(candidate_pauses))

    if owned_ratio < 0.1:
        score = 0
    elif owned_ratio < 0.3:
        score = 1
    elif owned_ratio < 0.5:
        score = 2
    elif owned_ratio < 0.7:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="OP", name="Owned Pause", category="Pauses & Silence", layer="D",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"owned_count": owned_count, "owned_ratio": round(owned_ratio, 3),
             "total_pauses": len(candidate_pauses)},
        evidence=[f"Owned={owned_count}", f"Ratio={owned_ratio:.1%}"],
        depends_on=["FP", "HP"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python op.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_op(report)
    print(json.dumps(result.to_dict(), indent=2))
