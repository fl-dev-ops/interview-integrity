"""Pau - Pause Quality (D): Whether pauses help or hurt communication."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.scoring import SignalResult, clamp_score, build_signal_context, PriorSignals
from utils.transcript import get_candidate_turns
from utils.llm import llm_call


def score_pau(report: dict, prior_signals: PriorSignals = None) -> SignalResult:
    turns = get_candidate_turns(report)
    if not turns:
        return SignalResult(code="Pau", name="Pause Quality", category="Pauses & Silence",
                            layer="D", source="transcript", score=0, confidence=0.3,
                            raw={}, evidence=["No turns"])

    pauses = report.get("pauses", [])
    candidate_pauses = [p for p in pauses if p.get("speaker") == "SPEAKER_0"]
    latency = report.get("latency", [])
    candidate_latencies = [l for l in latency if l.get("to_speaker") == "SPEAKER_0"]

    text = "\n".join(f"[Answer {i+1}] {t['text'][:400]}" for i, t in enumerate(turns[:6]))
    signal_ctx = build_signal_context(prior_signals, ["FP", "HP", "OP", "RP", "Lat", "Sil"])

    stats = (
        f"Total pauses: {len(candidate_pauses)}, "
        f"Long pauses (2.5s+): {sum(1 for p in candidate_pauses if p['duration'] > 2.5)}, "
        f"Avg latency: {sum(l['duration'] for l in candidate_latencies)/max(1,len(candidate_latencies)):.1f}s"
    )

    prompt = f"""Rate the overall pause quality of this interview candidate.
{"Use both the transcript evidence and the pre-computed signal scores below." if signal_ctx else ""}

{signal_ctx}

{stats}

Candidate answers:
{text}

Scoring guidelines:
- Your score should be CONSISTENT with the signal scores above (if provided).
- Use the transcript to confirm or contextualize the signals, not to contradict them.

Score on a 0-4 scale:
0: Pauses are disruptive or panicked
1: Frequent awkward or uncontrolled pauses
2: Mixed; some useful, some disruptive
3: Mostly calm and well placed
4: Deliberate, natural, and confidence-building

Return JSON: {{"score": <0-4>, "reasoning": "<brief>"}}"""

    raw = llm_call(prompt, system="You are an interview analysis expert. Return JSON only.")
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    result = json.loads(raw)

    return SignalResult(
        code="Pau", name="Pause Quality", category="Pauses & Silence", layer="D",
        source="llm", score=clamp_score(result["score"]), confidence=0.6,
        raw={"pause_count": len(candidate_pauses), **result},
        evidence=[result.get("reasoning", "")],
        depends_on=["FP", "HP", "OP", "RP", "Lat", "Sil"],
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pau.py <report.json>"); sys.exit(1)
    report = json.loads(Path(sys.argv[1]).read_text())
    result = score_pau(report)
    print(json.dumps(result.to_dict(), indent=2))
