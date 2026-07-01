from __future__ import annotations

import html
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKBONE_DIR = ROOT_DIR / "v1-llm-detection"
if str(BACKBONE_DIR) not in sys.path:
    sys.path.insert(0, str(BACKBONE_DIR))

from analyze_nlp import analyze as analyze_nlp  # noqa: E402
from fix_speakers import fix_session_speakers  # noqa: E402
from llm_detection import analyze_session  # noqa: E402
from pipeline import analyze as build_report_from_transcript  # noqa: E402
from pipeline import transcribe  # noqa: E402
from shared import (  # noqa: E402
    download_audio,
    get_openrouter_client,
    get_sarvam_client,
)

SPEAKER_MODEL = "openai/gpt-4o-mini"
LLM_MODEL = "openai/gpt-4o"


st.set_page_config(page_title="Interview Integrity Review", layout="wide")

st.markdown(
    """
    <style>
      .block-container { max-width: 1200px; padding-top: 2.5rem; }
      h1 { letter-spacing: -0.03em; }
      [data-testid="stMetricValue"] { font-size: 1.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

RISK_COLOR = {"High": "red", "Needs Review": "orange", "Low": "green"}
STATUS_COLOR = {"Needs attention": "red", "Mixed": "orange", "Consistent": "green"}


def badge(text: str, color_map: dict[str, str]) -> str:
    color = color_map.get(text, "gray")
    return f":{color}-background[**{text}**]"


def require_env() -> bool:
    missing = [
        key
        for key in ("SARVAM_API_KEY", "OPENROUTER_API_KEY")
        if not os.environ.get(key)
    ]
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


def format_timestamp(seconds: float | int | None) -> str:
    if seconds is None:
        return "--:--"
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def find_nlp_turn(
    nlp_result: dict[str, Any] | None, turn: dict[str, Any]
) -> dict[str, Any] | None:
    if not nlp_result:
        return None
    turn_id = turn.get("id")
    for item in nlp_result.get("turns", []):
        if item.get("turn_id") == turn_id:
            return item
    for item in nlp_result.get("turns", []):
        if item.get("speaker") == turn.get("speaker") and item.get("text") == turn.get(
            "text"
        ):
            return item
    return None


def find_llm_answer(
    llm_result: dict[str, Any] | None,
    turns: list[dict[str, Any]],
    selected_index: int,
    candidate_speaker: str,
) -> dict[str, Any] | None:
    if not llm_result:
        return None
    selected_turn = turns[selected_index]
    analyses = llm_result.get("per_answer_analysis", [])
    substantive_candidate_indices = [
        index
        for index, turn in enumerate(turns)
        if turn.get("speaker") == candidate_speaker
        and turn.get("word_count", len(turn.get("text", "").split())) >= 15
    ]
    substantive_candidate_ids = {
        turns[index].get("id") for index in substantive_candidate_indices
    }
    analysis_ids = [item.get("turn_id") for item in analyses]
    uses_transcript_turn_ids = bool(analysis_ids) and all(
        analysis_id in substantive_candidate_ids for analysis_id in analysis_ids
    )

    if uses_transcript_turn_ids:
        turn_id = selected_turn.get("id")
        for item in analyses:
            if item.get("turn_id") == turn_id:
                return item

    if selected_index not in substantive_candidate_indices:
        return None
    answer_ordinal = substantive_candidate_indices.index(selected_index) + 1
    for item in analyses:
        if item.get("turn_id") == answer_ordinal:
            return item
    if answer_ordinal <= len(analyses):
        return analyses[answer_ordinal - 1]
    return None


def nlp_flags_for_turn(
    nlp_result: dict[str, Any] | None, turn_id: int | None
) -> list[str]:
    if not nlp_result or turn_id is None:
        return []
    for item in nlp_result.get("flags", []):
        if item.get("turn_id") == turn_id:
            return item.get("flags", [])
    return []


def risk_label(score: float) -> str:
    if score >= 0.65:
        return "High"
    if score >= 0.35:
        return "Needs Review"
    return "Low"


def status_from_score(score: float) -> str:
    if score >= 0.65:
        return "Needs attention"
    if score >= 0.35:
        return "Mixed"
    return "Consistent"


def normalize_mismatch(value: Any) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "Not assessed"
    if score >= 7:
        return "Poor match"
    if score >= 4:
        return "Moderate match"
    return "Good match"


def build_turn_review(
    turn: dict[str, Any],
    nlp_turn: dict[str, Any] | None,
    llm_answer: dict[str, Any] | None,
    flags: list[str],
) -> dict[str, Any]:
    llm_score = float((llm_answer or {}).get("llm_score", 0) or 0)
    nlp_score = float((nlp_turn or {}).get("composite_score", 0) or 0)
    outlier = bool((nlp_turn or {}).get("outlier", {}).get("is_outlier"))
    likely_origin = (llm_answer or {}).get("likely_origin")
    specificity = (llm_answer or {}).get("specificity")
    structure = (llm_answer or {}).get("structural_pattern")
    register_match = (llm_answer or {}).get("register_match")
    vocabulary_match = (llm_answer or {}).get("vocabulary_match")

    score = max(llm_score, nlp_score)
    if outlier:
        score = max(score, 0.45)
    if likely_origin in {"llm_generated", "pre_written_script"}:
        score = max(score, 0.72)
    if specificity in {"low", "none"} and structure in {"template", "textbook"}:
        score = max(score, 0.55)
    score = min(score, 1.0)

    reasons = []
    if likely_origin == "llm_generated":
        reasons.append("The answer was assessed as likely LLM-assisted.")
    elif likely_origin == "pre_written_script":
        reasons.append(
            "The answer may be prepared or scripted rather than spontaneous."
        )
    elif likely_origin:
        reasons.append(
            f"The answer appears most consistent with {likely_origin.replace('_', ' ')} delivery."
        )

    try:
        if float(register_match or 0) >= 7:
            reasons.append("The speaking style differs from the candidate's baseline.")
    except (TypeError, ValueError):
        pass
    try:
        if float(vocabulary_match or 0) >= 7:
            reasons.append(
                "The vocabulary level differs from the candidate's baseline."
            )
    except (TypeError, ValueError):
        pass
    if specificity in {"low", "none"}:
        reasons.append("The response has limited concrete personal detail.")
    if structure in {"template", "textbook"}:
        reasons.append("The response structure sounds prepared or textbook-like.")
    if outlier:
        reasons.append(
            "The language pattern is unusual compared with nearby candidate responses."
        )
    reasons.extend(flags[:2])

    if not reasons:
        reasons.append(
            "This response is broadly consistent with the candidate's observed speaking pattern."
        )

    label = risk_label(score)
    if label == "High":
        action = "Review with the panel and ask a targeted follow-up question."
        summary = (
            "This response has stronger signs of being prepared or externally assisted."
        )
    elif label == "Needs Review":
        action = "Ask one follow-up question to verify the candidate's understanding."
        summary = "This response has mixed signals and is worth a closer look."
    else:
        action = "No immediate action needed. Keep as supporting context."
        summary = (
            "This response appears consistent with the candidate's interview pattern."
        )

    return {
        "turn_id": turn.get("id"),
        "risk_score": score,
        "risk_label": label,
        "primary_reason": reasons[0],
        "supporting_reasons": reasons,
        "summary": summary,
        "recommended_action": action,
        "style_match": normalize_mismatch(register_match),
        "vocabulary_match": normalize_mismatch(vocabulary_match),
        "specificity": (specificity or "Not assessed").replace("_", " ").title(),
        "structure": (structure or "Not assessed").replace("_", " ").title(),
        "likely_origin": (likely_origin or "Not assessed").replace("_", " ").title(),
        "llm_reasoning": (llm_answer or {}).get("reasoning"),
        "outlier": outlier,
    }


def build_review_model(
    report: dict[str, Any],
    nlp_result: dict[str, Any],
    llm_result: dict[str, Any],
) -> dict[str, Any]:
    turns = report.get("turns", [])
    candidate_speaker = nlp_result.get("student_speaker") or "SPEAKER_01"
    candidate_turn_reviews = {}
    candidate_indices = [
        index
        for index, turn in enumerate(turns)
        if turn.get("speaker") == candidate_speaker
    ]

    for index in candidate_indices:
        turn = turns[index]
        nlp_turn = find_nlp_turn(nlp_result, turn)
        llm_answer = find_llm_answer(llm_result, turns, index, candidate_speaker)
        flags = nlp_flags_for_turn(nlp_result, turn.get("id"))
        candidate_turn_reviews[index] = build_turn_review(
            turn, nlp_turn, llm_answer, flags
        )

    reviews = list(candidate_turn_reviews.values())
    high_count = sum(1 for review in reviews if review["risk_label"] == "High")
    review_count = sum(
        1 for review in reviews if review["risk_label"] == "Needs Review"
    )
    max_score = max((review["risk_score"] for review in reviews), default=0.0)
    verdict = llm_result.get("verdict", {})
    overall_score = max(float(verdict.get("confidence_score", 0) or 0), max_score)

    if high_count:
        assessment = "Likely Assisted or Prepared"
    elif review_count or overall_score >= 0.35:
        assessment = "Needs Review"
    else:
        assessment = "Likely Genuine"

    if assessment == "Likely Genuine":
        explanation = "The candidate's answers are mostly consistent with their observed speaking pattern."
    elif assessment == "Needs Review":
        explanation = "Some answers show mixed signals. A panelist should review the highlighted responses before deciding."
    else:
        explanation = "One or more answers show stronger signs of preparation or external assistance."

    summary = student_summary(nlp_result)[1]
    register_gap = summary.get("register_gap", {})
    evidence_summary = [
        {
            "title": "Voice Consistency",
            "status": status_from_score(max_score),
            "text": "Compares each answer against the candidate's natural speaking style in the interview.",
        },
        {
            "title": "Language Complexity",
            "status": status_from_score(
                float(summary.get("max_composite_score", 0) or 0)
            ),
            "text": "Looks for sudden changes in vocabulary, readability, or sentence structure.",
        },
        {
            "title": "Specificity",
            "status": "Needs attention"
            if any(r["specificity"] in {"Low", "None"} for r in reviews)
            else "Consistent",
            "text": "Checks whether answers include concrete personal details rather than generic explanations.",
        },
        {
            "title": "Interview Pattern",
            "status": status_from_score(float(verdict.get("confidence_score", 0) or 0)),
            "text": "Reviews whether concerns are isolated or repeat across the interview.",
        },
    ]

    flagged_indices = [
        index
        for index, review in candidate_turn_reviews.items()
        if review["risk_label"] in {"High", "Needs Review"}
    ]
    flagged_indices.sort(
        key=lambda index: candidate_turn_reviews[index]["risk_score"], reverse=True
    )

    return {
        "candidate_speaker": candidate_speaker,
        "assessment": assessment,
        "confidence": overall_score,
        "explanation": explanation,
        "answers_analyzed": llm_result.get(
            "substantive_answers_analyzed", len(candidate_indices)
        ),
        "responses_needing_review": len(flagged_indices),
        "candidate_turn_reviews": candidate_turn_reviews,
        "flagged_indices": flagged_indices,
        "evidence_summary": evidence_summary,
        "profile_summary": {
            "english": llm_result.get("speaker_profile", {}).get(
                "english_proficiency", "unknown"
            ),
            "register": llm_result.get("speaker_profile", {}).get(
                "natural_register", "unknown"
            ),
            "vocabulary": llm_result.get("speaker_profile", {}).get(
                "vocabulary_level", "unknown"
            ),
            "register_gap": register_gap,
        },
    }


def build_dashboard_data(
    report: dict[str, Any], review_model: dict[str, Any]
) -> dict[str, Any]:
    turns = report.get("turns", [])
    reviews = review_model["candidate_turn_reviews"]

    def detail(turn, review):
        return {
            "riskLabel": review.get("risk_label", "Not reviewed"),
            "riskScore": round(float(review.get("risk_score", 0) or 0), 2),
            "summary": review.get("summary", ""),
            "likelyOrigin": review.get("likely_origin", "Not assessed"),
            "reasons": review.get("supporting_reasons", []),
            "styleMatch": review.get("style_match", "Not assessed"),
            "vocabMatch": review.get("vocabulary_match", "Not assessed"),
            "specificity": review.get("specificity", "Not assessed"),
            "structure": review.get("structure", "Not assessed"),
            "llmReasoning": review.get("llm_reasoning") or "",
            "start": format_timestamp(turn.get("start")),
            "end": format_timestamp(turn.get("end")),
            "words": turn.get("word_count", len(turn.get("text", "").split())),
            "duration": f"{float(turn.get('duration', 0) or 0):.1f}s",
            "text": turn.get("text", "").strip(),
            "action": review.get("recommended_action", ""),
        }

    flagged = []
    for index in review_model["flagged_indices"]:
        turn = turns[index]
        review = reviews[index]
        flagged.append(
            {
                "riskLabel": review["risk_label"],
                "time": format_timestamp(turn.get("start")),
                "reason": review["primary_reason"],
                "preview": turn.get("text", "").strip(),
                "detail": detail(turn, review),
            }
        )

    candidate_speaker = review_model["candidate_speaker"]
    chat_turns = []
    for index, turn in enumerate(turns):
        speaker = turn.get("speaker", "unknown")
        is_candidate = speaker == candidate_speaker
        entry = {
            "speaker": "Candidate" if is_candidate else speaker,
            "isCandidate": is_candidate,
            "time": format_timestamp(turn.get("start")),
            "text": turn.get("text", "").strip(),
        }
        if is_candidate and index in reviews:
            review = reviews[index]
            entry["review"] = {
                "riskLabel": review["risk_label"],
                "reason": review["primary_reason"],
                "detail": detail(turn, review),
            }
        chat_turns.append(entry)

    speakers = sorted({t.get("speaker", "unknown") for t in turns})
    total_words = sum(
        t.get("word_count", len(t.get("text", "").split())) for t in turns
    )

    return {
        "assessment": review_model["assessment"],
        "confidence": round(review_model["confidence"], 2),
        "candidate": review_model["candidate_speaker"],
        "answersAnalyzed": review_model["answers_analyzed"],
        "needReview": review_model["responses_needing_review"],
        "explanation": review_model["explanation"],
        "evidence": review_model["evidence_summary"],
        "flagged": flagged,
        "turns": chat_turns,
        "stats": {
            "turns": len(turns),
            "speakers": len(speakers),
            "words": total_words,
            "overlaps": len(report.get("overlaps", [])),
        },
    }


DASHBOARD_TEMPLATE = """
<div id="app"></div>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: transparent; }
  #app {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #1a1a2e;
    background: transparent;
    padding: 0;
  }
  .tabs { display: flex; gap: 4px; border-bottom: 2px solid #e5e7eb; margin-bottom: 20px; }
  .tab-btn {
    padding: 10px 18px; border: none; background: none; cursor: pointer;
    font-size: 15px; font-weight: 600; color: #6b7280; border-bottom: 2px solid transparent;
    margin-bottom: -2px; transition: color .15s;
  }
  .tab-btn.active { color: #dc2626; border-bottom-color: #dc2626; }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }

  .card {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
    padding: 18px 20px; margin-bottom: 16px;
  }
  .card h3 { margin: 0 0 14px; font-size: 15px; font-weight: 700; }
  .stat-row { display: flex; gap: 28px; flex-wrap: wrap; }
  .stat-row-between { justify-content: space-between; }
  .stat { min-width: 110px; }
  .stat .label { font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .04em; font-weight: 600; }
  .stat .value { font-size: 20px; font-weight: 700; margin-top: 4px; }
  .explanation { margin-top: 14px; color: #4b5563; font-size: 14px; line-height: 1.6; }

  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
  @media (max-width: 900px) { .grid-4 { grid-template-columns: repeat(2, 1fr); } }
  .evidence-title { font-weight: 700; font-size: 14px; margin-bottom: 8px; }
  .evidence-text { font-size: 13px; color: #6b7280; margin-top: 8px; line-height: 1.5; }

  .pill {
    display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px;
    font-weight: 700; border: 1px solid transparent;
  }
  .pill-High, .pill-red, .pill-Needsattention { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
  .pill-NeedsReview, .pill-orange, .pill-Mixed { background: #fff7ed; color: #9a3412; border-color: #fed7aa; }
  .pill-Low, .pill-green, .pill-Consistent { background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
  .pill-gray { background: #f3f4f6; color: #374151; border-color: #e5e7eb; }

  .flag-row { cursor: pointer; }
  .flag-head { display: flex; align-items: center; gap: 12px; }
  .flag-time { color: #6b7280; font-size: 13px; font-weight: 600; }
  .flag-reason { font-weight: 700; font-size: 14px; flex: 1; }
  .flag-preview { color: #6b7280; font-size: 13px; margin-top: 8px; line-height: 1.5; }
  .flag-toggle { color: #dc2626; font-size: 13px; font-weight: 700; margin-top: 10px; }
  .flag-detail { display: none; margin-top: 14px; border-top: 1px solid #f0f0f0; padding-top: 14px; }
  .flag-row.open .flag-detail { display: block; }

  .detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 10px 0; }
  .detail-item { background: #f9fafb; border-radius: 10px; padding: 10px 12px; }
  .detail-item .label { font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; }
  .detail-item .value { font-size: 14px; font-weight: 700; margin-top: 3px; }
  .reasons { margin: 10px 0; padding-left: 18px; font-size: 13px; color: #374151; line-height: 1.7; }
  .response-text { background: #f9fafb; border-radius: 10px; padding: 12px 14px; font-size: 13.5px; line-height: 1.6; margin: 8px 0; }
  .action-box { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; border-radius: 10px; padding: 10px 14px; font-size: 13px; margin-top: 10px; }
  .sub-label { font-weight: 700; font-size: 13px; margin: 12px 0 4px; }

  .chat-wrap { padding: 6px 6px 6px 2px; }
  .msg-row { display: flex; margin-bottom: 14px; }
  .msg-row.candidate { justify-content: flex-end; }
  .bubble {
    max-width: 66%; padding: 12px 14px; border-radius: 14px; font-size: 14px; line-height: 1.55;
    background: #f3f4f6; border: 1px solid #e5e7eb;
  }
  .msg-row.candidate .bubble { background: #eef2ff; border-color: #e0e7ff; cursor: pointer; }
  .msg-meta { font-size: 11px; color: #9ca3af; margin-top: 6px; }
  .msg-review { margin-top: 8px; font-size: 12.5px; cursor: pointer; }
  .msg-review .flag-detail { max-width: 100%; }
</style>
<script>
const DATA = __DATA__;

function pillClass(text) {
  return "pill pill-" + text.replace(/\\s+/g, "");
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}

function renderDetail(d, idPrefix) {
  const reasons = (d.reasons || []).map(r => "<li>" + escapeHtml(r) + "</li>").join("");
  return `
    <div class="detail-grid">
      <div class="detail-item"><div class="label">Review status</div><div class="value">${escapeHtml(d.riskLabel)}</div></div>
      <div class="detail-item"><div class="label">Confidence</div><div class="value">${d.riskScore}</div></div>
    </div>
    <div style="font-size:13px;color:#374151;">${escapeHtml(d.summary)}</div>
    <div style="font-size:12px;color:#6b7280;margin-top:6px;">Likely origin: ${escapeHtml(d.likelyOrigin)}</div>
    <div class="sub-label">Why this matters</div>
    <ul class="reasons">${reasons}</ul>
    <div class="sub-label">Evidence breakdown</div>
    <div class="detail-grid">
      <div class="detail-item"><div class="label">Style match</div><div class="value">${escapeHtml(d.styleMatch)}</div></div>
      <div class="detail-item"><div class="label">Vocabulary match</div><div class="value">${escapeHtml(d.vocabMatch)}</div></div>
      <div class="detail-item"><div class="label">Specificity</div><div class="value">${escapeHtml(d.specificity)}</div></div>
      <div class="detail-item"><div class="label">Structure</div><div class="value">${escapeHtml(d.structure)}</div></div>
    </div>
    ${d.llmReasoning ? `<div style="font-size:12px;color:#6b7280;">${escapeHtml(d.llmReasoning)}</div>` : ""}
    <div class="sub-label">Candidate response</div>
    <div class="detail-grid">
      <div class="detail-item"><div class="label">Start</div><div class="value">${escapeHtml(d.start)}</div></div>
      <div class="detail-item"><div class="label">End</div><div class="value">${escapeHtml(d.end)}</div></div>
      <div class="detail-item"><div class="label">Words</div><div class="value">${d.words}</div></div>
      <div class="detail-item"><div class="label">Duration</div><div class="value">${escapeHtml(d.duration)}</div></div>
    </div>
    <div class="response-text">${escapeHtml(d.text)}</div>
    <div class="action-box">${escapeHtml(d.action)}</div>
  `;
}

function renderOverview() {
  const a = DATA;
  let html = `
    <div class="card">
      <h3>Overall Assessment</h3>
      <div class="stat-row stat-row-between">
        <div class="stat"><div class="label">Assessment</div><div class="value">${escapeHtml(a.assessment)}</div></div>
        <div class="stat"><div class="label">Confidence</div><div class="value">${a.confidence}</div></div>
      </div>
      <div class="explanation">${escapeHtml(a.explanation)}</div>
      <div class="explanation"><strong>How to read confidence:</strong> higher confidence means the review found stronger and more consistent signals for the assessment. Lower confidence means the evidence is mixed or limited, so the panel should treat the result as a prompt for follow-up rather than a conclusion.</div>
    </div>

    <div class="grid-4" style="margin-bottom:20px;">
  `;
  a.evidence.forEach(e => {
    html += `
      <div class="card" style="margin-bottom:0;">
        <div class="evidence-title">${escapeHtml(e.title)}</div>
        <div class="evidence-text">${escapeHtml(e.text)}</div>
        <div style="margin-top:12px;"><span class="${pillClass(e.status)}">${escapeHtml(e.status)}</span></div>
      </div>
    `;
  });
  html += `</div>`;
  document.getElementById("overview-pane").innerHTML = html;
}

function toggleFlag(i) {
  document.getElementById("flag-" + i).classList.toggle("open");
}

function toggleMsg(i) {
  document.getElementById("msg-review-" + i).classList.toggle("open");
}

function riskKey(label) {
  if (label === "High") return "high";
  if (label === "Needs Review") return "review";
  if (label === "Low") return "low";
  return "none";
}

function renderTranscript() {
  let html = `
    <div class="chat-wrap">
  `;
  DATA.turns.forEach((t, i) => {
    const risk = t.review ? riskKey(t.review.riskLabel) : "none";
    const bubbleClick = t.review ? ` onclick="toggleMsg(${i})"` : "";
    html += `<div class="msg-row ${t.isCandidate ? "candidate" : ""}" data-candidate="${t.isCandidate}" data-risk="${risk}">
      <div class="bubble"${bubbleClick}>
        <div>${escapeHtml(t.text)}</div>
        <div class="msg-meta">${escapeHtml(t.speaker)} · ${escapeHtml(t.time)}</div>`;
    if (t.review) {
      html += `<div class="msg-review flag-row" id="msg-review-${i}">
        <span class="${pillClass(t.review.riskLabel)}">${escapeHtml(t.review.riskLabel)}</span>
        &nbsp; ${escapeHtml(t.review.reason)}
        <div class="flag-detail" onclick="event.stopPropagation()">${renderDetail(t.review.detail)}</div>
      </div>`;
    }
    html += `</div></div>`;
  });
  html += `</div>`;
  document.getElementById("transcript-pane").innerHTML = html;
}

function showTab(name) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.toggle("active", p.id === name + "-pane"));
}

document.getElementById("app").innerHTML = `
  <div id="overview-pane"></div>
  <div id="transcript-pane"></div>
`;
renderOverview();
renderTranscript();
</script>
"""


def render_integrity_review(result: dict[str, Any]) -> None:
    review_model = build_review_model(
        result["report"], result["nlp_result"], result["llm_result"]
    )
    data = build_dashboard_data(result["report"], review_model)
    html_out = DASHBOARD_TEMPLATE.replace("__DATA__", json.dumps(data))
    component_height = 520 + len(data["turns"]) * 170 + len(data["flagged"]) * 120
    components.html(html_out, height=component_height, scrolling=False)


st.title("Interview Integrity Review")
st.caption(
    "Upload interview audio or paste an audio URL. The app summarizes whether candidate responses are consistent with the interview pattern."
)

uploaded_audio = st.file_uploader(
    "Upload audio", type=["mp3", "wav", "flac", "ogg", "m4a"]
)
audio_url = st.text_input("Or paste an audio URL", placeholder="https://...")

if st.button("Run full analysis", type="primary"):
    if uploaded_audio is None and not audio_url.strip():
        st.error("Upload an audio file or paste an audio URL.")
    elif uploaded_audio is not None and audio_url.strip():
        st.error("Use either an upload or a URL, not both.")
    elif require_env():
        try:
            with st.spinner("Running full detection pipeline..."):
                st.session_state["analysis_result"] = run_full_pipeline(
                    uploaded_audio, audio_url
                )
            st.success("Analysis complete.")
        except OSError as exc:
            st.error(f"Model/data dependency missing: {exc}")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

result = st.session_state.get("analysis_result")
if result:
    render_integrity_review(result)
