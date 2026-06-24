# Interview Diagnostics Bench

Interview audio analysis and feedback signal scoring.

## Repo Structure

```
bench/
├── data/                    # Sample data
│   └── samples-1/           # Sample 1: audio, transcript, report
│       ├── audio.mp3
│       ├── transcript.csv
│       ├── transcript.json
│       └── report.json
├── v1-llm-detection/        # V1: LLM-assisted detection pipeline
│   ├── pipeline.py
│   ├── shared.py
│   ├── analyze_nlp.py
│   ├── fix_speakers.py
│   ├── llm_detection.py
│   ├── process_users.py
│   ├── users.json
│   └── dimensions.md
├── v2-interview-signals/    # V2: Interview signal taxonomy
│   ├── scoring-spec.md
│   ├── periodic-table.html
│   ├── periodic-table.png
│   ├── rubric/
│   └── notebooks/
│       └── interview-signal-capture.ipynb
├── pyproject.toml
├── uv.lock
└── README.md
```

## Versions

### [V1: LLM-Assisted Detection](v1-llm-detection/)

Detect whether interview answers were LLM-assisted by analyzing register shifts, vocabulary anomalies, and linguistic patterns. Two-layer approach: 22 NLP features + 3-step LLM chain. See [`v1-llm-detection/README.md`](v1-llm-detection/README.md).

### [V2: Interview Signal Taxonomy](v2-interview-signals/)

A periodic-table-style taxonomy of every measurable signal from interview audio and transcript. Captures acoustic, timing, NLP, and semantic/rubric signals. See [`v2-interview-signals/README.md`](v2-interview-signals/README.md).

## Environment

Required in `.env` or environment:

```
SARVAM_API_KEY=...       # Sarvam AI for transcription
OPENROUTER_API_KEY=...   # OpenRouter for LLM analysis
```

## Quick Start

```bash
uv sync

# V1: Run the detection pipeline
uv run v1-llm-detection/process_users.py
uv run v1-llm-detection/process_users.py --skip-transcription --run-llm

# V2: Open the signal capture notebook
jupyter notebook v2-interview-signals/notebooks/interview-signal-capture.ipynb
```

## License

Private — for internal use.
