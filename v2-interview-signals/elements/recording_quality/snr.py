"""SNR - Signal-To-Noise Ratio (M): Voice signal strength relative to noise floor."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.audio import load_audio


def score_snr(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    snr = audio["snr_db_estimate"]

    if snr < 5:
        score = 0
    elif snr < 10:
        score = 1
    elif snr < 15:
        score = 2
    elif snr < 20:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="SNR", name="Signal-To-Noise Ratio", category="Recording Quality", layer="M",
        source="audio", score=clamp_score(score), confidence=0.9,
        raw={"snr_db": snr, "noise_floor": audio["noise_floor_rms"],
             "signal_level": audio["signal_level_rms"]},
        evidence=[f"SNR={snr:.1f}dB"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python snr.py <audio_path>"); sys.exit(1)
    result = score_snr(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
