# V1 Streamlit App

Streamlit UI for the full `v1-llm-detection` pipeline.

## Run

```bash
uv run streamlit run app/v1/streamlit_app.py
```

For NLP analysis, install the spaCy English model if it is not already present:

```bash
uv run python -m spacy download en_core_web_sm
```

## Input

Upload an interview audio file or paste an audio URL. The app runs every v1 stage:

- Sarvam transcription
- report generation
- OpenRouter speaker identification
- NLP detection
- OpenRouter LLM semantic detection

Required environment variables:

- `SARVAM_API_KEY`
- `OPENROUTER_API_KEY`
