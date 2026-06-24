"""Mic - Mic Quality (M): Clarity and fidelity of microphone capture."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.audio import load_audio


def score_mic(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    rms = audio["rms"]
    snr = audio["snr_db_estimate"]
    clip = audio["clipping_ratio"]
    peak = audio["peak"]

    if rms < 0.001 or snr < 3:
        score = 0
    elif rms < 0.005 or snr < 8:
        score = 1
    elif rms < 0.01 or snr < 12:
        score = 2
    elif rms >= 0.01 and snr >= 12 and clip < 0.01:
        score = 3
    else:
        score = 4 if clip < 0.001 and snr >= 18 else 3

    return SignalResult(
        code="Mic", name="Mic Quality", category="Recording Quality", layer="M",
        source="audio", score=clamp_score(score), confidence=0.8,
        raw={"rms": rms, "peak": peak, "snr_db": snr, "clip_ratio": clip},
        evidence=[f"RMS={rms:.4f}", f"SNR={snr:.1f}dB"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python mic.py <audio_path>"); sys.exit(1)
    result = score_mic(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
