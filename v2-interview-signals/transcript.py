#!/usr/bin/env python3
"""Download/transcribe audio and build a v2 report.json.

Outputs:
  - audio.mp3 (or source extension)
  - transcript.json (raw Sarvam response)
  - report.json (normalized segments/turns/latency/pauses/overlaps/stats)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.transcript import build_latency, build_overlaps, build_pauses, build_segments, build_turns


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def download_audio(source: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if source.startswith(("http://", "https://")):
        filename = source.split("/")[-1].split("?")[0] or "audio.mp3"
        if not any(filename.endswith(ext) for ext in (".mp3", ".wav", ".flac", ".ogg", ".m4a")):
            filename += ".mp3"
        dest = output_dir / filename
        if not dest.exists():
            urllib.request.urlretrieve(source, dest)
        return dest

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(source)
    dest = output_dir / source_path.name
    if not dest.exists():
        dest.write_bytes(source_path.read_bytes())
    return dest


def get_sarvam_client():
    from sarvamai import SarvamAI

    load_dotenv()
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY not found")
    return SarvamAI(api_subscription_key=api_key)


def transcribe(audio_path: Path, lang: str | None = None, speakers: int | None = None) -> dict:
    client = get_sarvam_client()
    params = {"model": "saaras:v3", "mode": "transcribe", "with_diarization": True}
    if lang:
        params["language_code"] = lang
    if speakers:
        params["num_speakers"] = speakers

    print(f"Transcribing {audio_path.name} with Sarvam Saaras v3")
    job = client.speech_to_text_job.create_job(**params)
    job.upload_files(file_paths=[str(audio_path)])
    start = time.perf_counter()
    job.start()
    job.wait_until_complete()
    print(f"  Done in {time.perf_counter() - start:.1f}s")

    file_results = job.get_file_results()
    if file_results.get("failed"):
        raise RuntimeError(file_results["failed"])

    tmp_dir = audio_path.parent / "_sarvam_tmp"
    tmp_dir.mkdir(exist_ok=True)
    job.download_outputs(output_dir=str(tmp_dir))
    result_files = sorted(tmp_dir.glob("*.json"))
    if not result_files:
        raise RuntimeError("No output JSON from Sarvam")
    data = json.loads(result_files[0].read_text(encoding="utf-8"))
    for path in result_files:
        path.unlink()
    tmp_dir.rmdir()
    return data


def distribution(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean": 0, "median": 0, "p25": 0, "p75": 0, "min": 0, "max": 0, "values": []}
    values = sorted(values)
    def percentile(p: int) -> float:
        if len(values) == 1:
            return values[0]
        k = (len(values) - 1) * (p / 100)
        lo = int(k)
        hi = min(lo + 1, len(values) - 1)
        return values[lo] + (k - lo) * (values[hi] - values[lo])
    return {
        "count": len(values),
        "mean": round(sum(values) / len(values), 2),
        "median": round(percentile(50), 2),
        "p25": round(percentile(25), 2),
        "p75": round(percentile(75), 2),
        "min": round(values[0], 2),
        "max": round(values[-1], 2),
        "values": [round(v, 2) for v in values],
    }


def compute_stats(turns: list[dict], latencies: list[dict], pauses: list[dict]) -> dict:
    speakers: dict[str, dict] = {}
    for turn in turns:
        speaker = turn["speaker"]
        speakers.setdefault(speaker, {"turn_count": 0, "total_speaking_time": 0.0, "total_words": 0, "latencies": [], "pauses": [], "words": [], "durations": []})
        stats = speakers[speaker]
        stats["turn_count"] += 1
        stats["total_speaking_time"] += turn["duration"]
        stats["total_words"] += turn["word_count"]
        stats["words"].append(turn["word_count"])
        stats["durations"].append(turn["duration"])
    for latency in latencies:
        if latency["to_speaker"] in speakers:
            speakers[latency["to_speaker"]]["latencies"].append(latency["duration"])
    for pause in pauses:
        if pause["speaker"] in speakers:
            speakers[pause["speaker"]]["pauses"].append(pause["duration"])
    return {
        speaker: {
            "turn_count": data["turn_count"],
            "total_speaking_time": round(data["total_speaking_time"], 2),
            "total_words": data["total_words"],
            "latency": distribution(data["latencies"]),
            "pause": distribution(data["pauses"]),
            "words": distribution(data["words"]),
            "duration": distribution(data["durations"]),
        }
        for speaker, data in speakers.items()
    }


def build_report(transcript_data: dict) -> dict:
    entries = transcript_data["diarized_transcript"]["entries"]
    segments = build_segments(entries)
    turns = build_turns(segments)
    latency = build_latency(turns)
    pauses = build_pauses(segments, turns)
    overlaps = build_overlaps(segments)
    return {
        "segments": segments,
        "turns": turns,
        "latency": latency,
        "pauses": pauses,
        "overlaps": overlaps,
        "stats": compute_stats(turns, latency, pauses),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create transcript.json and report.json for v2 scoring")
    parser.add_argument("source", help="Audio URL or local audio path")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--lang", default=None)
    parser.add_argument("--speakers", type=int, default=None)
    args = parser.parse_args()

    audio_path = download_audio(args.source, args.output_dir)
    transcript_data = transcribe(audio_path, lang=args.lang, speakers=args.speakers)
    transcript_path = args.output_dir / "transcript.json"
    transcript_path.write_text(json.dumps(transcript_data, indent=2, ensure_ascii=False), encoding="utf-8")

    report = build_report(transcript_data)
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {transcript_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
