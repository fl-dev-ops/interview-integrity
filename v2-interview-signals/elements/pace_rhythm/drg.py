"""Drg - Dragging (D): Frequency/severity of too-slow speech. Higher = less dragging."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, PriorSignals
from utils.transcript import get_candidate_turns


def score_drg(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Drg", name="Dragging", category="Pace & Rhythm",
                            layer="D", source="transcript", score=3, confidence=0.3,
                            raw={}, evidence=["No turns"])

    wpm_list = []
    for t in turns:
        if t["duration"] > 0:
            wpm_list.append(t["word_count"] / (t["duration"] / 60))

    drag_count = sum(1 for w in wpm_list if w < 90)
    drag_ratio = drag_count / max(1, len(wpm_list))
    avg_wpm = sum(wpm_list) / max(1, len(wpm_list))

    if drag_ratio > 0.6 or avg_wpm < 70:
        score = 0
    elif drag_ratio > 0.4 or avg_wpm < 90:
        score = 1
    elif drag_ratio > 0.2 or avg_wpm < 100:
        score = 2
    elif drag_ratio > 0.05:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Drg", name="Dragging", category="Pace & Rhythm", layer="D",
        source="transcript", score=clamp_score(score), confidence=0.8,
        raw={"avg_wpm": round(avg_wpm, 1), "drag_count": drag_count,
             "drag_ratio": round(drag_ratio, 3), "wpm_list": [round(w, 1) for w in wpm_list]},
        evidence=[f"Avg WPM={avg_wpm:.1f}", f"Drag ratio={drag_ratio:.1%}"],
        depends_on=["WPM"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python drg.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_drg(report)
    print(json.dumps(result.to_dict(), indent=2))
