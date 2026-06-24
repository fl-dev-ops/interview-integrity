"""Dia - Diarization (M): Ability to separate speakers accurately."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns, get_interviewer_turns


def score_dia(report: dict) -> SignalResult:
    turns = report.get("turns", [])
    if not turns:
        return SignalResult(code="Dia", name="Diarization", category="Recording Quality",
                            layer="M", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    speakers = set(t["speaker"] for t in turns)
    cand_turns = get_candidate_turns(report)
    int_turns = get_interviewer_turns(report)
    overlaps = report.get("overlaps", [])
    candidate_overlaps = [o for o in overlaps if "SPEAKER_0" in (o.get("speaker_a", ""), o.get("speaker_b", ""))]
    overlap_duration = sum(o["duration"] for o in candidate_overlaps)

    total_duration = max(1.0, turns[-1]["end"] - turns[0]["start"]) if turns else 1.0
    overlap_ratio = overlap_duration / total_duration

    if len(speakers) < 2 or overlap_ratio > 0.15:
        score = 0
    elif overlap_ratio > 0.08:
        score = 1
    elif overlap_ratio > 0.04:
        score = 2
    elif overlap_ratio > 0.01:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Dia", name="Diarization", category="Recording Quality", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.7,
        raw={"speakers": len(speakers), "cand_turns": len(cand_turns), "int_turns": len(int_turns),
             "overlap_count": len(candidate_overlaps), "overlap_ratio": round(overlap_ratio, 4)},
        evidence=[f"Speakers={len(speakers)}", f"Overlap={overlap_ratio:.1%}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python dia.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_dia(report)
    print(json.dumps(result.to_dict(), indent=2))
