from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKBONE_DIR = ROOT_DIR / "v1-llm-detection"
if str(BACKBONE_DIR) not in sys.path:
    sys.path.insert(0, str(BACKBONE_DIR))

from analyze_nlp import analyze as analyze_nlp  # noqa: E402
from fix_speakers import fix_session_speakers  # noqa: E402
from llm_detection import analyze_session  # noqa: E402
from pipeline import analyze as build_report_from_transcript  # noqa: E402
from pipeline import transcribe  # noqa: E402
from shared import download_audio, get_openrouter_client, get_sarvam_client  # noqa: E402


SPEAKER_MODEL = "openai/gpt-4o-mini"
LLM_MODEL = "openai/gpt-4o"


st.set_page_config(page_title="V1 LLM Detection", layout="wide")


def require_env() -> bool:
    missing = [key for key in ("SARVAM_API_KEY", "OPENROUTER_API_KEY") if not os.environ.get(key)]
    if missing:
        st.error(f"Missing required environment variable(s): {', '.join(missing)}")
        return False
    return True


def create_session_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="v1_llm_detection_"))


def prepare_audio(session_dir: Path, uploaded_file, audio_url: str) -> Path:
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix or ".mp3"
        audio_path = session_dir / f"uploaded_audio{suffix}"
        audio_path.write_bytes(uploaded_file.getvalue())
        return audio_path

    return download_audio(audio_url.strip(), session_dir)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_full_pipeline(uploaded_file, audio_url: str) -> dict[str, Any]:
    session_dir = create_session_dir()
    sarvam_client = get_sarvam_client()
    openrouter_client = get_openrouter_client()

    progress = st.progress(0, text="Preparing audio...")
    audio_path = prepare_audio(session_dir, uploaded_file, audio_url)

    progress.progress(15, text="Transcribing with Sarvam...")
    transcript = transcribe(audio_path, client=sarvam_client, lang=None, speakers=None)
    transcript_path = session_dir / "transcript.json"
    write_json(transcript_path, transcript)

    progress.progress(35, text="Building report...")
    report = build_report_from_transcript(transcript)
    report_path = session_dir / "report.json"
    write_json(report_path, report)

    progress.progress(50, text="Identifying interviewer and candidate...")
    speaker_result = fix_session_speakers(
        session_dir,
        client=openrouter_client,
        model=SPEAKER_MODEL,
    )
    report = read_json(report_path)

    progress.progress(65, text="Running NLP detection...")
    nlp_result = analyze_nlp(report, use_perplexity=True)
    nlp_path = session_dir / "nlp_report.json"
    write_json(nlp_path, nlp_result)

    progress.progress(82, text="Running LLM semantic detection...")
    llm_result = analyze_session(report_path, model=LLM_MODEL, client=openrouter_client)
    llm_path = session_dir / "llm.json"
    write_json(llm_path, llm_result)

    progress.progress(100, text="Analysis complete.")
    return {
        "session_dir": str(session_dir),
        "audio_path": str(audio_path),
        "speaker_result": speaker_result,
        "report": report,
        "nlp_result": nlp_result,
        "llm_result": llm_result,
    }


def student_summary(nlp_result: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    student = nlp_result.get("student_speaker")
    summaries = nlp_result.get("session_analysis", {})
    if student in summaries:
        return student, summaries[student]
    if summaries:
        speaker, summary = max(
            summaries.items(),
            key=lambda item: item[1].get("substantive_turns", 0),
        )
        return speaker, summary
    return None, {}


def score_label(score: float) -> str:
    if score >= 0.5:
        return "High"
    if score >= 0.3:
        return "Medium"
    return "Low"


def render_report_overview(report: dict[str, Any]) -> None:
    turns = report.get("turns", [])
    speakers = sorted({turn.get("speaker", "unknown") for turn in turns})
    total_words = sum(turn.get("word_count", len(turn.get("text", "").split())) for turn in turns)

    st.subheader("Transcript")
    cols = st.columns(4)
    cols[0].metric("Turns", len(turns))
    cols[1].metric("Speakers", len(speakers))
    cols[2].metric("Words", total_words)
    cols[3].metric("Overlaps", len(report.get("overlaps", [])))

    with st.expander("Transcript turns", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "turn": turn.get("id"),
                        "speaker": turn.get("speaker"),
                        "start": turn.get("start"),
                        "end": turn.get("end"),
                        "words": turn.get("word_count"),
                        "text": turn.get("text"),
                    }
                    for turn in turns
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_nlp_results(nlp_result: dict[str, Any]) -> None:
    student, summary = student_summary(nlp_result)
    score = float(summary.get("max_composite_score", 0) or 0)

    st.subheader("NLP Detection")
    cols = st.columns(5)
    cols[0].metric("Candidate speaker", student or "unknown")
    cols[1].metric("Risk", score_label(score))
    cols[2].metric("Max score", f"{score:.2f}")
    cols[3].metric("Avg score", f"{float(summary.get('avg_composite_score', 0) or 0):.2f}")
    cols[4].metric("Outlier turns", summary.get("outlier_turn_count", 0))

    register_gap = summary.get("register_gap", {})
    st.caption(
        "Register gap: "
        f"formality {register_gap.get('formality_gap', 0)}, "
        f"zipf {register_gap.get('zipf_gap', 0)}, "
        f"FK grade {register_gap.get('fk_grade_gap', 0)}"
    )

    turn_rows = [
        {
            "turn": turn.get("turn_id"),
            "speaker": turn.get("speaker"),
            "type": turn.get("turn_type"),
            "words": turn.get("word_count"),
            "score": turn.get("composite_score"),
            "outlier": turn.get("outlier", {}).get("is_outlier", False),
            "text": turn.get("text"),
        }
        for turn in nlp_result.get("turns", [])
    ]
    if turn_rows:
        st.dataframe(
            pd.DataFrame(turn_rows).sort_values("score", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    flags = nlp_result.get("flags", [])
    if flags:
        with st.expander("Flag details", expanded=True):
            for flag in flags:
                st.markdown(f"**Turn {flag['turn_id']} ({flag['speaker']})**")
                for item in flag.get("flags", []):
                    st.write(f"- {item}")


def render_llm_results(llm_result: dict[str, Any]) -> None:
    verdict = llm_result.get("verdict", {})
    st.subheader("LLM Semantic Detection")

    cols = st.columns(4)
    cols[0].metric("Assessment", verdict.get("assessment", "unknown"))
    cols[1].metric("Confidence score", f"{float(verdict.get('confidence_score', 0) or 0):.2f}")
    cols[2].metric("Answers analyzed", llm_result.get("substantive_answers_analyzed", 0))
    cols[3].metric("Suspicious turns", len(verdict.get("suspicious_turn_ids", [])))

    st.write(verdict.get("reasoning", "No reasoning returned."))

    answers = llm_result.get("per_answer_analysis", [])
    if answers:
        st.dataframe(pd.DataFrame(answers), use_container_width=True, hide_index=True)


def render_downloads(result: dict[str, Any]) -> None:
    cols = st.columns(3)
    cols[0].download_button(
        "Download report.json",
        data=json.dumps(result["report"], indent=2, ensure_ascii=False),
        file_name="report.json",
        mime="application/json",
    )
    cols[1].download_button(
        "Download nlp_report.json",
        data=json.dumps(result["nlp_result"], indent=2, ensure_ascii=False),
        file_name="nlp_report.json",
        mime="application/json",
    )
    cols[2].download_button(
        "Download llm.json",
        data=json.dumps(result["llm_result"], indent=2, ensure_ascii=False),
        file_name="llm.json",
        mime="application/json",
    )


st.title("V1 LLM-Assisted Answer Detection")
st.caption("Upload interview audio or paste an audio URL. The app runs transcription, speaker identification, NLP scoring, and LLM detection.")

uploaded_audio = st.file_uploader("Upload audio", type=["mp3", "wav", "flac", "ogg", "m4a"])
audio_url = st.text_input("Or paste an audio URL", placeholder="https://...")

if st.button("Run full analysis", type="primary"):
    if uploaded_audio is None and not audio_url.strip():
        st.error("Upload an audio file or paste an audio URL.")
    elif uploaded_audio is not None and audio_url.strip():
        st.error("Use either an upload or a URL, not both.")
    elif require_env():
        try:
            with st.spinner("Running full detection pipeline..."):
                st.session_state["analysis_result"] = run_full_pipeline(uploaded_audio, audio_url)
            st.success("Analysis complete.")
        except OSError as exc:
            st.error(f"Model/data dependency missing: {exc}")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

result = st.session_state.get("analysis_result")
if result:
    speaker_result = result.get("speaker_result", {})
    st.info(
        "Speaker mapping: "
        f"{speaker_result.get('status', 'unknown')} "
        f"(confidence: {speaker_result.get('confidence', 'n/a')})"
    )
    render_llm_results(result["llm_result"])
    render_nlp_results(result["nlp_result"])
    render_report_overview(result["report"])
    render_downloads(result)
