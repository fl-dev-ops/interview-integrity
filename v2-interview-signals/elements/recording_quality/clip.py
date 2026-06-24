"""Clip - Clipping (M): Distorted peaks from overly loud signal. Higher = less clipping."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.audio import load_audio


def score_clip(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    clip_ratio = audio["clipping_ratio"]

    if clip_ratio > 0.05:
        score = 0
    elif clip_ratio > 0.02:
        score = 1
    elif clip_ratio > 0.005:
        score = 2
    elif clip_ratio > 0.001:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Clip", name="Clipping", category="Recording Quality", layer="M",
        source="audio", score=clamp_score(score), confidence=0.9,
        raw={"clipping_ratio": clip_ratio, "peak": audio["peak"]},
        evidence=[f"Clip ratio={clip_ratio:.4f}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python clip.py <audio_path>"); sys.exit(1)
    result = score_clip(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
