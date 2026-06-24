#!/usr/bin/env python3
"""Runner: Compute all interview signal elements for a given recording."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.audio import load_audio
from utils.html_report import generate_periodic_table_html, generate_slide_deck_html
from utils.transcript import load_report

AUDIO_ELEMENTS = {"VOL", "PRJ", "SNR", "DROP", "CLIP", "MIC", "NOI"}
AUDIO_LLM_ELEMENTS = {"VAR", "STE", "TON", "EN", "CLR", "MON", "ECHO"}

# Dependency graph — maps element code to its upstream dependencies.
# Used for topological execution order so composites receive prior scores.
ELEMENT_DEPENDENCIES: dict[str, list[str]] = {
    "CONF": ["VOL", "STE", "PAC", "PAU", "HOLD", "RECV", "PRES"],
    "COMP": ["REL", "EX", "ACT", "JUD", "IMP"],
    "STAR": ["CTX", "ACT", "RES", "STR"],
    "STR": ["CTX", "ACT", "RES"],
    "SENT": ["GRM"],
    "COH": ["CONN"],
    "FLO": ["FS", "REP", "SC"],
    "NERV": ["FP", "HP"],
    "GRM": ["TEN", "SVA"],
    "DET": ["NUM", "NAM"],
    "RECV": ["RP", "SC"],
    "REC": ["SC", "RP"],
    "PAU": ["FP", "HP", "OP", "RP", "LAT", "SIL"],
    "RHY": ["PAC"],
    "PAC": ["WPM", "RUS", "DRG"],
    "RUS": ["WPM"],
    "DRG": ["WPM"],
    "OP": ["FP", "HP"],
    "RP": ["OP"],
    "HP": ["FP"],
}


def run_all(audio_path: Path, report_path: Path, output_path: Path | None = None) -> list[dict]:
    report = load_report(report_path)

    audio_data = None
    if audio_path and audio_path.exists():
        audio_data = load_audio(audio_path)

    # Upload audio to Google GenAI once for all audio LLM elements
    google_file = None
    if audio_path and audio_path.exists():
        try:
            from utils.llm import upload_audio_for_scoring
            google_file = upload_audio_for_scoring(audio_path)
            print(f"Uploaded audio to Google GenAI Files API")
        except Exception as e:
            print(f"Warning: Failed to upload audio to Google: {e}")

    from elements.voice_delivery import ALL_VOICE_DELIVERY
    from elements.pace_rhythm import ALL_PACE_RHYTHM
    from elements.pauses_silence import ALL_PAUSES_SILENCE
    from elements.fluency import ALL_FLUENCY
    from elements.language_quality import ALL_LANGUAGE_QUALITY
    from elements.answer_structure import ALL_ANSWER_STRUCTURE
    from elements.specificity import ALL_SPECIFICITY
    from elements.reasoning import ALL_REASONING
    from elements.conversation_behavior import ALL_CONVERSATION_BEHAVIOR
    from elements.confidence_signals import ALL_CONFIDENCE_SIGNALS
    from elements.role_competency import ALL_ROLE_COMPETENCY
    from elements.recording_quality import ALL_RECORDING_QUALITY

    all_scorers = (
        ALL_VOICE_DELIVERY + ALL_PACE_RHYTHM + ALL_PAUSES_SILENCE + ALL_FLUENCY +
        ALL_LANGUAGE_QUALITY + ALL_ANSWER_STRUCTURE + ALL_SPECIFICITY + ALL_REASONING +
        ALL_CONVERSATION_BEHAVIOR + ALL_CONFIDENCE_SIGNALS + ALL_ROLE_COMPETENCY +
        ALL_RECORDING_QUALITY
    )

    # Topological sort so dependencies are computed before dependents
    from utils.scoring import topo_sort_scorers, scorer_accepts_prior_signals
    ordered_scorers = topo_sort_scorers(all_scorers, ELEMENT_DEPENDENCIES)

    results = []
    results_by_code: dict[str, Any] = {}  # code -> SignalResult for prior_signals
    for scorer in ordered_scorers:
        name = scorer.__name__.replace("score_", "").upper()
        try:
            # Build prior_signals from completed dependencies
            deps = ELEMENT_DEPENDENCIES.get(name, [])
            prior = {dep: results_by_code[dep] for dep in deps if dep in results_by_code}
            prior_arg = prior if prior and scorer_accepts_prior_signals(scorer) else None

            if name in AUDIO_ELEMENTS:
                result = scorer(audio_path)
            elif name in AUDIO_LLM_ELEMENTS:
                if prior_arg:
                    result = scorer(report, audio_path, google_file, prior_signals=prior_arg)
                else:
                    result = scorer(report, audio_path, google_file)
            else:
                if prior_arg:
                    result = scorer(report, prior_signals=prior_arg)
                else:
                    result = scorer(report)
            results.append(result.to_dict())
            results_by_code[name] = result
        except Exception as e:
            results.append({"code": name, "error": str(e)})

    # Cleanup uploaded file
    if google_file:
        from utils.llm import cleanup_uploaded_file
        cleanup_uploaded_file(google_file)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
        print(f"Wrote {len(results)} results to {output_path}")
        html_path = output_path.with_suffix(".html")
        generate_periodic_table_html(results, html_path)
        print(f"Wrote scored HTML report to {html_path}")
        slides_path = output_path.with_name(f"{output_path.stem}_slides.html")
        generate_slide_deck_html(results, slides_path)
        print(f"Wrote slide HTML report to {slides_path}")
        canonical_html_path = Path(__file__).resolve().parent / "periodic-table-scored.html"
        if canonical_html_path != html_path.resolve():
            generate_periodic_table_html(results, canonical_html_path)
            print(f"Updated latest scored HTML report at {canonical_html_path}")
        canonical_slides_path = Path(__file__).resolve().parent / "periodic-table-slides.html"
        if canonical_slides_path != slides_path.resolve():
            generate_slide_deck_html(results, canonical_slides_path)
            print(f"Updated latest slide HTML report at {canonical_slides_path}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run.py <audio_path> <report.json> [output.json]")
        sys.exit(1)

    audio = Path(sys.argv[1])
    report = Path(sys.argv[2])
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    run_all(audio, report, output)
