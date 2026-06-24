"""Scoring utilities for interview signal elements."""

from __future__ import annotations

import inspect
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class SignalResult:
    code: str
    name: str
    category: str
    layer: str  # M, D, J, C
    source: str
    score: int  # 0-4
    raw: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.7
    evidence: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "layer": self.layer,
            "source": self.source,
            "score": self.score,
            "raw": self.raw,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "depends_on": self.depends_on,
        }


AudioPath = Path
TranscriptPath = Path
ReportPath = Path

# Type alias for prior signals passed to scorers
PriorSignals = dict[str, SignalResult] | None


def clamp_score(x: float) -> int:
    return int(max(0, min(4, round(x))))


def avg_score(*vals: float | None) -> int:
    present = [v for v in vals if v if v is not None]
    return clamp_score(sum(present) / len(present)) if present else 0


def pct(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return float(s[f] + (k - f) * (s[c] - s[f]))


def distribution(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean": 0, "median": 0, "p25": 0, "p75": 0, "min": 0, "max": 0, "values": []}
    return {
        "count": len(values),
        "mean": round(sum(values) / len(values), 2),
        "median": round(pct(values, 50), 2),
        "p25": round(pct(values, 25), 2),
        "p75": round(pct(values, 75), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "values": [round(v, 2) for v in values],
    }


def band_score(value: float, bands: list[tuple[float, int]]) -> int:
    for threshold, score in bands:
        if value <= threshold:
            return score
    return bands[-1][1] if bands else 0


def scorer_accepts_prior_signals(fn: Callable) -> bool:
    """Check if a scorer function accepts a prior_signals parameter."""
    sig = inspect.signature(fn)
    return "prior_signals" in sig.parameters


def topo_sort_scorers(
    scorers: list[Callable],
    dependencies: dict[str, list[str]],
) -> list[Callable]:
    """Sort scorers by dependency order using Kahn's algorithm.

    Args:
        scorers: List of scorer functions.
        dependencies: Map of element code -> list of dependency codes.

    Returns:
        Scorers in topological order (dependencies first).
    """
    # Build code -> scorer map
    scorer_by_code: dict[str, Callable] = {}
    for s in scorers:
        code = s.__name__.replace("score_", "").upper()
        scorer_by_code[code] = s

    # Build in-degree map
    in_degree: dict[str, int] = {c: 0 for c in scorer_by_code}
    graph: dict[str, list[str]] = {c: [] for c in scorer_by_code}

    for code, deps in dependencies.items():
        if code not in scorer_by_code:
            continue
        for dep in deps:
            if dep in graph:
                graph[dep].append(code)
                in_degree[code] += 1

    # Kahn's algorithm
    queue = deque(c for c, d in in_degree.items() if d == 0)
    sorted_codes: list[str] = []

    while queue:
        node = queue.popleft()
        sorted_codes.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_codes) != len(scorer_by_code):
        # Cycle detected — fall back to original order
        return scorers

    return [scorer_by_code[c] for c in sorted_codes]


def build_signal_context(prior_signals: PriorSignals, codes: list[str]) -> str:
    """Build a formatted signal context block for LLM prompts.

    Args:
        prior_signals: Dict of code -> SignalResult from prior computations.
        codes: Which signal codes to include in the context.

    Returns:
        Formatted string block, or empty string if no prior signals.
    """
    if not prior_signals:
        return ""

    lines = []
    for code in codes:
        if code in prior_signals:
            s = prior_signals[code]
            evidence = ", ".join(s.evidence[:2]) if s.evidence else ""
            lines.append(f"  {code} ({s.name}): {s.score}/4 — {evidence}")

    if not lines:
        return ""

    return (
        "=== Pre-computed Signal Scores (0-4 scale) ===\n"
        + "\n".join(lines)
    )
