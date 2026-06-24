"""Audio loading and analysis utilities."""

from __future__ import annotations

import math
from pathlib import Path

from utils.scoring import pct, distribution


def load_audio(path: Path) -> dict:
    """Load audio and compute basic waveform metrics."""
    import torch
    import torchaudio

    waveform, sr = torchaudio.load(str(path))
    mono = waveform.mean(dim=0)
    duration = mono.numel() / sr

    abs_x = mono.abs()
    rms = torch.sqrt(torch.mean(mono ** 2)).item()
    peak = abs_x.max().item()

    clipping_ratio = float((abs_x > 0.98).float().mean().item())

    frame = max(1, int(sr * 0.05))
    frames = mono[: (mono.numel() // frame) * frame].reshape(-1, frame) if mono.numel() >= frame else mono.reshape(1, -1)
    frame_rms = torch.sqrt(torch.mean(frames ** 2, dim=1)).numpy().tolist()

    noise_floor = pct(frame_rms, 10)
    signal_level = pct(frame_rms, 90)
    snr_db = 20 * math.log10((signal_level + 1e-9) / (noise_floor + 1e-9))

    silence_threshold = max(noise_floor * 1.8, rms * 0.18)
    silence_ratio = sum(1 for v in frame_rms if v < silence_threshold) / max(1, len(frame_rms))

    return {
        "duration_seconds": round(duration, 2),
        "sample_rate": sr,
        "channels": int(waveform.shape[0]),
        "rms": round(rms, 6),
        "peak": round(peak, 6),
        "clipping_ratio": round(clipping_ratio, 6),
        "noise_floor_rms": round(noise_floor, 6),
        "signal_level_rms": round(signal_level, 6),
        "snr_db_estimate": round(snr_db, 2),
        "silence_ratio_estimate": round(silence_ratio, 4),
        "frame_rms": frame_rms,
        "mono": mono,
    }


def get_candidate_segments(audio_data: dict, report: dict, candidate: str = "SPEAKER_0") -> list[dict]:
    """Extract candidate audio segments based on report turns."""
    import torch

    mono = audio_data["mono"]
    sr = audio_data["sample_rate"]
    segments = []

    for turn in report.get("turns", []):
        if turn["speaker"] != candidate:
            continue
        start_i = max(0, int(turn["start"] * sr))
        end_i = min(mono.numel(), int(turn["end"] * sr))
        seg = mono[start_i:end_i]
        if seg.numel() == 0:
            continue
        seg_rms = torch.sqrt(torch.mean(seg ** 2)).item()
        segments.append({"turn_id": turn["id"], "rms": round(seg_rms, 6), "duration": turn["duration"]})

    return segments
