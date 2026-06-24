# TODO — Deferred Items

## Problem 4: Threshold Calibration (Deferred)
**Status:** Circle back after Problems 2, 3, 5, 7, 8 are fixed.
**Issue:** All scoring thresholds (WPM bands, filler rates, pause durations, etc.) are hardcoded magic numbers with no empirical calibration.
**What's needed:**
- Collect scored samples across diverse candidates (different roles, languages, experience levels)
- Compare automated scores against human evaluator scores
- Tune thresholds to match human judgment
- Consider per-role or per-band thresholds (junior vs senior, tech vs non-tech)
- Consider language-specific thresholds (English-native vs L2 speakers)
**Blocked by:** Need the signal pipeline to be correct first (audio working, bias fixed, composites composing).

## Problem 6: Test Coverage (Pinned)
**Status:** Pin for later — after implementation changes stabilize.
**Issue:** Zero test coverage on deterministic scorers.
**What's needed:**
- Unit tests for all programmatic elements (WPM, FP, HP, Lat, Sil, FS, Rep, Frag, etc.)
- Unit tests for `utils/transcript.py` helpers (count_fillers, count_connectors, tokenize_words, build_qa_pairs)
- Unit tests for `utils/scoring.py` (clamp_score, band_score, avg_score, pct)
- Unit tests for `utils/audio.py` (load_audio metrics)
- Integration test: run full pipeline on sample-1, verify output schema
- Regression test: pin sample-1 scores as baseline, detect drift
**Blocked by:** Need to finish code changes first, then freeze and test.

## Problem 8: Linguistic Bias — Multilingual Fairness (Deferred)
**Status:** Circle back — needs a scalable approach, not hardcoded word lists.
**Issue:** The system penalizes non-native English speakers. Fillers, connectors, fragment detection, false-start detection, and LLM prompts all assume English-only input. Indian multilingual candidates (Hindi-English, Tamil-English, etc.) get systematically lower scores.
**Why deferred:** The initial approach (hardcoded filler/connector word lists per language) won't scale to the diversity of Indian languages and dialects. Need a more general solution.
**What's needed:**
- A language-agnostic approach to filler detection (e.g., statistical models, not word lists)
- Language detection or script detection as metadata (not as scoring input)
- LLM prompts that explicitly handle multilingual/code-switching context without needing to enumerate languages
- Consider: can the LLM itself handle multilingual fairness if given the right instructions? (i.e., fix the prompts, not the regex)
- Consider: Sarvam's `translit` mode vs `transcribe` mode — romanized output may simplify processing
**Blocked by:** Need to understand the actual transcript quality and language mix in real data first.
