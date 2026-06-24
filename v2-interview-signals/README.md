# V2: Interview Signal Taxonomy

The new interview feedback signal system — a periodic-table-style taxonomy of every measurable signal from audio and transcript.

## What It Does

Captures and scores every element of interview performance through four routes:

- **Acoustic programmatic evaluation** — volume, SNR, clipping, noise, dropouts
- **Transcript/timing programmatic evaluation** — WPM, latency, pauses, overlaps, turn-taking
- **Transcript NLP evaluation** — vocabulary, grammar, repetition, connectors, formality
- **LLM-powered semantic/rubric evaluation** — relevance, reasoning, judgment, impact, trust

## Key Insight

From only an audio file + diarized transcript, every value in the signal table can be captured. The system explicitly labels each element by layer:

| Layer | Code | Meaning |
|-------|------|---------|
| Raw Metric | `M` | Directly measured from audio/transcript |
| Derived Signal | `D` | Calculated from multiple metrics |
| Judgment Signal | `J` | Requires semantic/contextual interpretation |
| Composite Signal | `C` | Combines multiple signals |

## Files

| File | Description |
|------|-------------|
| `scoring-spec.md` | Scoring spec for every element (type, criteria, dependencies) |
| `periodic-table.html` | Editable source for the periodic table poster |
| `periodic-table.png` | Latest periodic table image |
| `periodic-table-early-draft.png` | Earlier draft for reference |
| `rubric/feedback-cards.md` | Feedback cards mapped to rubric |
| `rubric/feedback-cards-mapped-to-rubric.pdf` | Original rubric PDF |
| `run.py` | CLI runner — compute all elements for a recording |
| `notebooks/interview-signal-capture.ipynb` | Main notebook — end-to-end signal capture |
| `notebooks/prototype-notebook.py` | Earlier prototype for reference |

## Element Architecture

Each element has its own Python file under `elements/<category>/`:

```
elements/
  voice_delivery/   Vol, Var, Ste, Ton, Prj, En, Clr, Mon
  pace_rhythm/      WPM, Acc, Dec, Rus, Drg, Pac, Rhy
  pauses_silence/   FP, HP, Lat, Sil, OP, RP, Pau
  fluency/          FS, Rep, SC, Run, Frag, Flo, Coh, Conn
  language_quality/ Grm, Ten, SVA, Sent, Voc, Reg, Tech, Idi, RepW, Pwr, Gap
  answer_structure/ Str, Ctx, Act, Res, Ex, STAR, Rel, Drf
  specificity/      Ver, Step, Num, Nam, Det, Con
  reasoning/        Why, C&E, Opt, Trd, Jud, Ins, Ref, Beyond
  conversation_behavior/ Adp, Ask, B&F, Lis, Ans, Turn, Rec
  confidence_signals/ Trust, Pres, Hold, Recv, Own, Conf, Nerv
  role_competency/  Imp, Lead, Prof, Prob, Coll, Learn, Comp
  recording_quality/ Dia, SNR, Drop, Clip, Echo, Mic, Noi
```

Each element file:
- Recomputes from inputs every time (no stale data)
- Has `if __name__ == "__main__"` for standalone CLI usage
- Returns a `SignalResult` with score, raw data, evidence, and dependencies

### LLM routing

| Signal type | Client | When |
|-------------|--------|------|
| Audio file analysis | Google GenAI SDK + Files API | When audio file is needed |
| Text-only semantic scoring | OpenRouter via OpenAI SDK | All J-layer elements |

### Running all elements

```bash
cd v2-interview-signals
python3 run.py ../data/samples-1/audio.mp3 ../data/samples-1/report.json output.json
```

Or run a single element:

```bash
python3 elements/pace_rhythm/wpm.py ../data/samples-1/report.json
python3 elements/recording_quality/snr.py ../data/samples-1/audio.mp3
```

## Notebook Structure

The notebook `interview-signal-capture.ipynb` runs in stages:

| Stage | Section | Description |
|-------|---------|-------------|
| 0 | Setup & Paths | Config, helpers, API clients |
| 1 | Transcription | Sarvam diarized transcription |
| 2 | Transcript Normalization | Segments, turns, latency, pauses, overlaps, stats |
| 3 | Speaker Role Identification | Always LLM — identifies interviewer/candidate |
| 4 | QA Pair Construction | Question-answer pairs for semantic scoring |
| 5 | Acoustic Metrics | Audio-only features from raw waveform |
| 6 | Timing & Conversation Metrics | WPM, latency, pauses, fillers, turn-taking |
| 7 | Transcript/NLP Metrics | Language quality features from transcript |
| 8 | Semantic LLM Rubric Scoring | Meaning-heavy rubric elements via LLM |
| 9 | Derived & Composite Signals | Combines all metrics into signal report |
| 10 | Review Tables | Summary tables and visualizations |

Sections from 3 onward reload inputs from disk, so they are independently runnable after stage 2.

## Output

All artifacts are written to `data/samples-N/v2_outputs/`:

- `transcript.json`
- `report.json`
- `speaker_roles.json`
- `report.roles.json`
- `qa_pairs.json`
- `audio_metrics.json`
- `timing_metrics.json`
- `nlp_metrics.json`
- `semantic_scores.json`
- `signal_report.json` — the final scored signal report
