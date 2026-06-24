"""Drop - Dropouts (M): Missing audio chunks, glitches, or packet loss. Higher = fewer dropouts."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score
from utils.audio import load_audio


def score_drop(audio_path: Path) -> SignalResult:
    audio = load_audio(audio_path)
    frame_rms = audio["frame_rms"]

    if not frame_rms:
        return SignalResult(code="Drop", name="Dropouts", category="Recording Quality",
                            layer="M", source="audio", score=2, confidence=0.3,
                            raw={}, evidence=["No frame data"])

    zero_frames = sum(1 for v in frame_rms if v < 0.0001)
    dropout_ratio = zero_frames / max(1, len(frame_rms))

    if dropout_ratio > 0.1:
        score = 0
    elif dropout_ratio > 0.05:
        score = 1
    elif dropout_ratio > 0.02:
        score = 2
    elif dropout_ratio > 0.005:
        score = 3
    else:
        score = 4

    return SignalResult(
        code="Drop", name="Dropouts", category="Recording Quality", layer="M",
        source="audio", score=clamp_score(score), confidence=0.8,
        raw={"zero_frames": zero_frames, "dropout_ratio": round(dropout_ratio, 4)},
        evidence=[f"Zero frames={zero_frames}", f"Ratio={dropout_ratio:.2%}"],
        depends_on=[],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python drop.py <audio_path>"); sys.exit(1)
    result = score_drop(Path(sys.argv[1]))
    print(json.dumps(result.to_dict(), indent=2))
