"""Vol - Volume (M): Loudness / audibility level."""

from __future__ import annotations

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, pct
from utils.audio import load_audio


def score_vol(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    rms = audio["rms"]
    peak = audio["peak"]
    clip = audio["clipping_ratio"]
    duration = audio["duration_seconds"]

    values = audio["frame_rms"]
    p10 = pct(values, 10)
    p90 = pct(values, 90)

    if p10 < 0.001 and p90 < 0.005:
        score = 0
    elif clip > 0.01 or p90 > 0.95:
        score = 1
    elif rms < 0.005 or p90 < 0.02:
        score = 1
    elif rms < 0.01 or p90 < 0.05:
        score = 2
    elif rms < 0.05 and clip < 0.001:
        score = 3
    else:
        score = 4 if clip < 0.0001 and rms >= 0.01 else 3

    return SignalResult(
        code="Vol", name="Volume", category="Voice Delivery", layer="M",
        source="audio", score=clamp_score(score), confidence=0.8,
        raw={"rms": rms, "peak": peak, "clip_ratio": clip, "p10": p10, "p90": p90},
        evidence=[f"RMS={rms:.4f}", f"Peak={peak:.4f}", f"Clip={clip:.4f}"],
    )


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python vol.py <audio_path>"); sys.exit(1)
    result = score_vol(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
