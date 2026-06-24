"""Prj - Projection (D): Perceived voice carrying power and audibility."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.audio import load_audio


def score_prj(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    rms = audio["rms"]
    peak = audio["peak"]
    clip = audio["clipping_ratio"]
    snr = audio["snr_db_estimate"]
    p10 = audio["noise_floor_rms"]
    p90 = audio["signal_level_rms"]

    if rms < 0.002 or snr < 5:
        score = 0
    elif rms < 0.005 or snr < 10:
        score = 1
    elif rms < 0.01 or snr < 15:
        score = 2
    elif rms >= 0.01 and snr >= 15 and clip < 0.005:
        score = 3
    else:
        score = 4 if clip < 0.001 and snr >= 20 else 3

    return SignalResult(
        code="Prj", name="Projection", category="Voice Delivery", layer="D",
        source="audio", score=clamp_score(score), confidence=0.8,
        raw={"rms": rms, "peak": peak, "snr_db": snr, "clip_ratio": clip},
        evidence=[f"RMS={rms:.4f}", f"SNR={snr:.1f}dB", f"Clip={clip:.4f}"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python prj.py <audio_path>"); sys.exit(1)
    result = score_prj(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
