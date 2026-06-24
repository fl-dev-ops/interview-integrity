"""Sil - Long Silence (M): Silent gaps above threshold, e.g. 2.5s+. Higher = fewer harmful silences."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.transcript import get_candidate_turns


def score_sil(report: dict, threshold: float = 2.5) -> SignalResult:
    pauses = report.get("pauses", [])
    candidate_pauses = [p for p in pauses if p.get("speaker") == "SPEAKER_0"]

    long_pauses = [p for p in candidate_pauses if p["duration"] >= threshold]
    total_candidate_time = sum(t["duration"] for t in get_candidate_turns(report))
    long_ratio = len(long_pauses) / max(1, len(candidate_pauses)) if candidate_pauses else 0
    long_total = sum(p["duration"] for p in long_pauses)

    if len(long_pauses) > 5 or long_ratio > 0.5:
        score = 0
    elif len(long_pauses) > 3 or long_ratio > 0.3:
        score = 1
    elif len(long_pauses) > 1:
        score = 2
    elif len(long_pauses) > 0:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Sil", name="Long Silence", category="Pauses & Silence", layer="M",
        source="transcript", score=clamp_score(score), confidence=0.85,
        raw={"long_pause_count": len(long_pauses), "long_pause_ratio": round(long_ratio, 3),
             "long_pause_total_s": round(long_total, 2), "threshold_s": threshold},
        evidence=[f"Long pauses={len(long_pauses)}", f"Ratio={long_ratio:.1%}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sil.py <report.json> [threshold]"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    thresh = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
    result = score_sil(report, threshold=thresh)
    print(json.dumps(result.to_dict(), indent=2))
