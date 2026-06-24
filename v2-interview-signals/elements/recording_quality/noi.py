"""Noi - Noise (M): Background noise level and intrusiveness. Higher = less harmful noise."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.audio import load_audio


def score_noi(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    noise_floor = audio["noise_floor_rms"]
    rms = audio["rms"]
    snr = audio["snr_db_estimate"]

    if noise_floor > 0.05 or snr < 5:
        score = 0
    elif noise_floor > 0.02 or snr < 10:
        score = 1
    elif noise_floor > 0.01 or snr < 15:
        score = 2
    elif noise_floor > 0.005:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Noi", name="Noise", category="Recording Quality", layer="M",
        source="audio", score=clamp_score(score), confidence=0.8,
        raw={"noise_floor": noise_floor, "rms": rms, "snr_db": snr},
        evidence=[f"Noise floor={noise_floor:.4f}", f"SNR={snr:.1f}dB"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python noi.py <audio_path>"); sys.exit(1)
    result = score_noi(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
