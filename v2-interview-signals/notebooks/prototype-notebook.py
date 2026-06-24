import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Interview Signal Capture Notebook

    This notebook demonstrates the full path from one audio file to a scored signal report.

    Core idea: after **Step 2**, we have canonical inputs: `audio` + `transcript/report`. From that point, every value in the interview signal table is capturable through one of four routes:

    - acoustic programmatic evaluation
    - transcript/timing programmatic evaluation
    - transcript NLP evaluation
    - LLM-powered semantic/rubric evaluation

    Sections from Step 3 onward reload their own inputs from disk so they are independently runnable after `report.json` exists.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 0. Setup & Paths
    """)
    return


@app.cell
def _():
    from __future__ import annotations

    import csv
    import json
    import math
    import os
    import re
    import statistics
    import subprocess
    import sys
    import time
    from pathlib import Path
    from typing import Any

    ROOT = Path.cwd()
    AUDIO_PATH = ROOT / 'temp' / 'audio.mp3'
    CSV_TRANSCRIPT_PATH = ROOT / 'temp' / 'transcript.csv'
    WORK_DIR = ROOT / 'temp' / 'notebook_outputs'
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    TRANSCRIPT_PATH = WORK_DIR / 'transcript.json'
    REPORT_PATH = WORK_DIR / 'report.json'
    SPEAKER_ROLES_PATH = WORK_DIR / 'speaker_roles.json'
    TRANSCRIPT_ROLES_PATH = WORK_DIR / 'transcript.roles.json'
    REPORT_ROLES_PATH = WORK_DIR / 'report.roles.json'
    QA_PAIRS_PATH = WORK_DIR / 'qa_pairs.json'
    AUDIO_METRICS_PATH = WORK_DIR / 'audio_metrics.json'
    TIMING_METRICS_PATH = WORK_DIR / 'timing_metrics.json'
    NLP_METRICS_PATH = WORK_DIR / 'nlp_metrics.json'
    SEMANTIC_SCORES_PATH = WORK_DIR / 'semantic_scores.json'
    SIGNAL_REPORT_PATH = WORK_DIR / 'signal_report.json'

    FORCE_TRANSCRIBE = False
    FORCE_LLM = False

    def load_dotenv(path: Path = ROOT / '.env') -> None:
        if not path.exists():
            return
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip().strip('\"').strip("'"))

    def save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def load_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding='utf-8'))

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
            return {'count': 0, 'mean': 0, 'median': 0, 'p25': 0, 'p75': 0, 'min': 0, 'max': 0, 'values': []}
        return {
            'count': len(values),
            'mean': round(sum(values) / len(values), 2),
            'median': round(pct(values, 50), 2),
            'p25': round(pct(values, 25), 2),
            'p75': round(pct(values, 75), 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'values': [round(v, 2) for v in values],
        }

    load_dotenv()
    print('Audio:', AUDIO_PATH, AUDIO_PATH.exists())
    print('Work dir:', WORK_DIR)
    return (
        AUDIO_METRICS_PATH,
        AUDIO_PATH,
        CSV_TRANSCRIPT_PATH,
        FORCE_LLM,
        FORCE_TRANSCRIBE,
        NLP_METRICS_PATH,
        Path,
        QA_PAIRS_PATH,
        REPORT_PATH,
        REPORT_ROLES_PATH,
        SEMANTIC_SCORES_PATH,
        SIGNAL_REPORT_PATH,
        SPEAKER_ROLES_PATH,
        TIMING_METRICS_PATH,
        TRANSCRIPT_PATH,
        WORK_DIR,
        csv,
        distribution,
        json,
        load_json,
        math,
        os,
        pct,
        re,
        save_json,
        statistics,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 0.1 API Clients
    """)
    return


@app.cell
def _(json, os):
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'

    def get_sarvam_client(api_key: str | None = None):
        from sarvamai import SarvamAI
        api_key = api_key or os.environ.get('SARVAM_API_KEY')
        if not api_key:
            raise RuntimeError('SARVAM_API_KEY not found. Set it in .env or environment.')
        return SarvamAI(api_subscription_key=api_key)

    def get_openrouter_client(api_key: str | None = None):
        from openai import OpenAI
        api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise RuntimeError('OPENROUTER_API_KEY not found. Set it in .env or environment.')
        return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)

    def llm_json_call(client, model: str, system_prompt: str, user_prompt: str, schema: dict, name: str) -> dict:
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
            response_format={'type': 'json_schema', 'json_schema': {'name': name, 'strict': True, 'schema': schema}},
            temperature=0.0,
            extra_body={'provider': {'require_parameters': True}, 'plugins': [{'id': 'response-healing'}]},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError('Empty LLM response')
        return json.loads(content)

    return get_openrouter_client, get_sarvam_client, llm_json_call


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Transcription

    Creates `transcript.json`. Uses Sarvam diarized transcription. If `transcript.json` already exists, it is reused unless `FORCE_TRANSCRIBE = True`.
    """)
    return


@app.cell
def _(
    AUDIO_PATH,
    FORCE_TRANSCRIBE,
    Path,
    TRANSCRIPT_PATH,
    WORK_DIR,
    get_sarvam_client,
    load_json,
    save_json,
    time,
):
    def transcribe_with_sarvam(audio_path: Path, client, lang: str | None = None, speakers: int | None = None) -> dict:
        job_params = {'model': 'saaras:v3', 'mode': 'transcribe', 'with_diarization': True}
        if lang:
            job_params['language_code'] = lang
        if speakers:
            job_params['num_speakers'] = speakers

        print('Transcribing with Sarvam Saaras v3...')
        job = client.speech_to_text_job.create_job(**job_params)
        job.upload_files(file_paths=[str(audio_path)])
        start = time.perf_counter()
        job.start()
        job.wait_until_complete()
        print(f'Done in {time.perf_counter() - start:.1f}s')

        file_results = job.get_file_results()
        if file_results.get('failed'):
            raise RuntimeError(file_results['failed'])

        tmp_dir = WORK_DIR / '_sarvam_tmp'
        tmp_dir.mkdir(exist_ok=True)
        job.download_outputs(output_dir=str(tmp_dir))
        result_files = sorted(tmp_dir.glob('*.json'))
        if not result_files:
            raise RuntimeError('No output JSON from Sarvam')
        data = load_json(result_files[0])
        for p in result_files:
            p.unlink()
        tmp_dir.rmdir()
        return data

    if TRANSCRIPT_PATH.exists() and not FORCE_TRANSCRIBE:
        transcript_data = load_json(TRANSCRIPT_PATH)
        print('Reusing existing transcript:', TRANSCRIPT_PATH)
    else:
        sarvam_client = get_sarvam_client()
        transcript_data = transcribe_with_sarvam(AUDIO_PATH, sarvam_client)
        save_json(TRANSCRIPT_PATH, transcript_data)
        print('Saved:', TRANSCRIPT_PATH)

    list(transcript_data.keys())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Transcript Normalization

    Creates `report.json`: segments, turns, latencies, pauses, overlaps, and speaker stats. This is the canonical checkpoint. After this, sections should be independently runnable.
    """)
    return


@app.cell
def _(
    CSV_TRANSCRIPT_PATH,
    Path,
    REPORT_PATH,
    TRANSCRIPT_PATH,
    csv,
    distribution,
    load_json,
    save_json,
):
    def build_segments(entries: list[dict]) -> list[dict]:
        return [{'speaker': f"SPEAKER_{e['speaker_id']}" if not str(e['speaker_id']).startswith('SPEAKER_') else str(e['speaker_id']), 'start': round(float(e['start_time_seconds']), 2), 'end': round(float(e['end_time_seconds']), 2), 'text': e.get('transcript', '').strip()} for e in entries if e.get('transcript', '').strip()]

    def finalize_turn(raw: dict, turn_id: int) -> dict:
        text = ' '.join(raw['texts']).strip()
        duration = max(0.0, raw['end'] - raw['start'])
        return {'id': turn_id, 'speaker': raw['speaker'], 'start': raw['start'], 'end': raw['end'], 'segment_ids': raw['segment_ids'], 'text': text, 'word_count': len(text.split()), 'duration': round(duration, 2)}

    def build_turns(segments: list[dict]) -> list[dict]:
        if not segments:
            return []
        turns = []
        current = {'speaker': segments[0]['speaker'], 'start': segments[0]['start'], 'end': segments[0]['end'], 'texts': [segments[0]['text']], 'segment_ids': [0]}
        for i, seg in enumerate(segments[1:], start=1):
            if seg['speaker'] == current['speaker']:
                current['end'] = seg['end']
                current['texts'].append(seg['text'])
                current['segment_ids'].append(i)
            else:
                turns.append(finalize_turn(current, len(turns) + 1))
                current = {'speaker': seg['speaker'], 'start': seg['start'], 'end': seg['end'], 'texts': [seg['text']], 'segment_ids': [i]}
        turns.append(finalize_turn(current, len(turns) + 1))
        return turns

    def build_latency(turns: list[dict]) -> list[dict]:
        out = []
        for prev, curr in zip(turns, turns[1:]):
            if prev['speaker'] != curr['speaker']:
                out.append({'from_turn_id': prev['id'], 'to_turn_id': curr['id'], 'from_speaker': prev['speaker'], 'to_speaker': curr['speaker'], 'duration': round(curr['start'] - prev['end'], 2)})
        return out

    def build_pauses(segments: list[dict], turns: list[dict]) -> list[dict]:
        pauses = []
        for turn in turns:
            for prev_id, curr_id in zip(turn['segment_ids'], turn['segment_ids'][1:]):
                gap = round(segments[curr_id]['start'] - segments[prev_id]['end'], 2)
                if gap > 0:
                    pauses.append({'turn_id': turn['id'], 'speaker': turn['speaker'], 'start': segments[prev_id]['end'], 'end': segments[curr_id]['start'], 'duration': gap})
        return pauses

    def build_overlaps(segments: list[dict]) -> list[dict]:
        overlaps = []
        for i, a in enumerate(segments):
            for j in range(i + 1, len(segments)):
                b = segments[j]
                if b['start'] >= a['end']:
                    break
                if a['speaker'] == b['speaker']:
                    continue
                start, end = (max(a['start'], b['start']), min(a['end'], b['end']))
                if end > start:
                    overlaps.append({'segment_a': i, 'segment_b': j, 'speaker_a': a['speaker'], 'speaker_b': b['speaker'], 'start': round(start, 2), 'end': round(end, 2), 'duration': round(end - start, 2)})
        return overlaps

    def compute_stats(turns: list[dict], latencies: list[dict], pauses: list[dict]) -> dict:
        speakers = {}
        for turn in turns:
            sp = turn['speaker']
            speakers.setdefault(sp, {'turn_count': 0, 'total_speaking_time': 0.0, 'total_words': 0, '_latencies': [], '_pauses': [], '_word_counts': [], '_durations': []})
            speakers[sp]['turn_count'] += 1
            speakers[sp]['total_speaking_time'] += turn['duration']
            speakers[sp]['total_words'] += turn['word_count']
            speakers[sp]['_word_counts'].append(turn['word_count'])
            speakers[sp]['_durations'].append(turn['duration'])
        for lat in latencies:
            speakers.get(lat['to_speaker'], {}).get('_latencies', []).append(lat['duration'])
        for pause in pauses:
            speakers.get(pause['speaker'], {}).get('_pauses', []).append(pause['duration'])
        return {sp: {'turn_count': d['turn_count'], 'total_speaking_time': round(d['total_speaking_time'], 2), 'total_words': d['total_words'], 'latency': distribution(d['_latencies']), 'pause': distribution(d['_pauses']), 'words': distribution(d['_word_counts']), 'duration': distribution(d['_durations'])} for sp, d in speakers.items()}

    def analyze_transcript_data(data: dict) -> dict:
        entries = data.get('diarized_transcript', {}).get('entries', [])
        if not entries:
            raise ValueError('No diarized_transcript.entries found')
        segments = build_segments(entries)
        turns = build_turns(segments)
        latencies = build_latency(turns)
        pauses = build_pauses(segments, turns)
        overlaps = build_overlaps(segments)
        return {'segments': segments, 'turns': turns, 'latency': latencies, 'pauses': pauses, 'overlaps': overlaps, 'stats': compute_stats(turns, latencies, pauses)}

    def csv_transcript_to_report(path: Path) -> dict:
        rows = list(csv.DictReader(path.open()))
        turns = []
        for i, row in enumerate(rows, start=1):
            mm, ss = row['Timestamp'].split(':')
            start = int(mm) * 60 + int(ss)
            end = int(rows[i]['Timestamp'].split(':')[0]) * 60 + int(rows[i]['Timestamp'].split(':')[1]) if i < len(rows) else start + 2
            text = row['Transcript'].strip()
            turns.append({'id': i, 'speaker': row['Speaker'], 'start': float(start), 'end': float(end), 'segment_ids': [i - 1], 'text': text, 'word_count': len(text.split()), 'duration': round(max(0, end - start), 2)})
        segments = [{'speaker': t['speaker'], 'start': t['start'], 'end': t['end'], 'text': t['text']} for t in turns]
        latencies = build_latency(turns)
        pauses = []
        overlaps = []
        return {'segments': segments, 'turns': turns, 'latency': latencies, 'pauses': pauses, 'overlaps': overlaps, 'stats': compute_stats(turns, latencies, pauses), 'source': 'csv_fallback'}
    if TRANSCRIPT_PATH.exists():
        _report = analyze_transcript_data(load_json(TRANSCRIPT_PATH))
    elif CSV_TRANSCRIPT_PATH.exists():
        print('Using CSV fallback because transcript.json is not available')
        _report = csv_transcript_to_report(CSV_TRANSCRIPT_PATH)
    else:
        raise FileNotFoundError('Need transcript.json or temp/transcript.csv')
    save_json(REPORT_PATH, _report)
    print('Saved:', REPORT_PATH)
    print('Turns:', len(_report['turns']), 'Speakers:', sorted(_report['stats'].keys()))
    _report['turns'][:3]
    return (compute_stats,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Speaker Role Identification - Always LLM

    Independently runnable after Step 2. Loads `report.json` and uses an LLM to identify interviewer/candidate. Writes role-normalized files instead of mutating originals.
    """)
    return


@app.cell
def _(
    FORCE_LLM,
    REPORT_PATH,
    REPORT_ROLES_PATH,
    SPEAKER_ROLES_PATH,
    compute_stats,
    get_openrouter_client,
    json,
    llm_json_call,
    load_json,
    save_json,
):
    def speaker_id_schema() -> dict:
        return {'type': 'object', 'properties': {'interviewer_speaker_id': {'type': 'string'}, 'candidate_speaker_id': {'type': 'string'}, 'confidence': {'type': 'number'}, 'reasoning': {'type': 'string'}}, 'required': ['interviewer_speaker_id', 'candidate_speaker_id', 'confidence', 'reasoning'], 'additionalProperties': False}

    def identify_speakers_llm(report: dict, model: str='openai/gpt-4o-mini') -> dict:
        client = get_openrouter_client()
        speaker_turns = {}
        for t in _report['turns']:
            speaker_turns.setdefault(t['speaker'], [])
            if len(speaker_turns[t['speaker']]) < 5:
                speaker_turns[t['speaker']].append(t)
        lines = []
        for sp in sorted(speaker_turns):
            lines.append(f'\n--- {sp} ---')
            for t in speaker_turns[sp]:
                lines.append(f"[{t['id']}] {t['word_count']} words: {t['text'][:450]}")
        sample = '\n'.join(lines)
        system = 'You identify interviewer and candidate roles in an interview transcript. Return only JSON.'
        user = f'Identify which speaker is the interviewer and which speaker is the candidate/student.\n\nRules:\n- Interviewer asks questions and guides the session.\n- Candidate answers, describes background, projects, skills, and experience.\n\nTranscript sample:\n{sample}'
        return llm_json_call(client, model, system, user, speaker_id_schema(), 'SpeakerIdentification')

    def build_speaker_mapping(roles: dict) -> dict:
        return {roles['interviewer_speaker_id']: 'SPEAKER_00', roles['candidate_speaker_id']: 'SPEAKER_01'}

    def canonicalize_report(report: dict, roles: dict) -> dict:
        mapping = build_speaker_mapping(roles)
        aliases = {}
        for old, new in mapping.items():
            aliases[old] = new
            if old.startswith('SPEAKER_'):
                aliases[old.replace('SPEAKER_', '')] = new
            else:
                aliases[f'SPEAKER_{old}'] = new
        copied = json.loads(json.dumps(_report))
        for key in ['segments', 'turns']:
            for item in copied.get(key, []):
                item['speaker'] = aliases.get(item['speaker'], item['speaker'])
        for lat in copied.get('latency', []):
            lat['from_speaker'] = aliases.get(lat['from_speaker'], lat['from_speaker'])
            lat['to_speaker'] = aliases.get(lat['to_speaker'], lat['to_speaker'])
        for pause in copied.get('pauses', []):
            pause['speaker'] = aliases.get(pause['speaker'], pause['speaker'])
        for ov in copied.get('overlaps', []):
            ov['speaker_a'] = aliases.get(ov['speaker_a'], ov['speaker_a'])
            ov['speaker_b'] = aliases.get(ov['speaker_b'], ov['speaker_b'])
        copied['stats'] = compute_stats(copied['turns'], copied.get('latency', []), copied.get('pauses', []))
        copied['speaker_roles'] = {'SPEAKER_00': 'interviewer', 'SPEAKER_01': 'candidate', 'llm_identification': roles}
        return copied
    _report = load_json(REPORT_PATH)
    if SPEAKER_ROLES_PATH.exists() and (not FORCE_LLM):
        roles = load_json(SPEAKER_ROLES_PATH)
        print('Reusing:', SPEAKER_ROLES_PATH)
    else:
        roles = identify_speakers_llm(_report)
        save_json(SPEAKER_ROLES_PATH, roles)
    role_report = canonicalize_report(_report, roles)
    save_json(REPORT_ROLES_PATH, role_report)
    print('Roles:', roles)
    print('Saved:', REPORT_ROLES_PATH)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. QA Pair Construction

    Independently runnable. Builds question-answer pairs from `report.roles.json` for semantic scoring.
    """)
    return


@app.cell
def _(QA_PAIRS_PATH, REPORT_PATH, REPORT_ROLES_PATH, load_json, save_json):
    def build_qa_pairs(report: dict, interviewer: str='SPEAKER_00', candidate: str='SPEAKER_01') -> list[dict]:
        pairs = []
        turns = _report['turns']
        for i, turn in enumerate(turns):
            if turn['speaker'] != candidate:
                continue
            question = None
            for prev in reversed(turns[:i]):
                if prev['speaker'] == interviewer:
                    question = prev
                    break
            pairs.append({'question_turn_id': question['id'] if question else None, 'answer_turn_id': turn['id'], 'question': question['text'] if question else '', 'answer': turn['text'], 'answer_start': turn['start'], 'answer_end': turn['end'], 'duration': turn['duration'], 'word_count': turn['word_count']})
        return pairs
    _report = load_json(REPORT_ROLES_PATH if REPORT_ROLES_PATH.exists() else REPORT_PATH)
    _qa_pairs = build_qa_pairs(_report)
    save_json(QA_PAIRS_PATH, _qa_pairs)
    print('Saved:', QA_PAIRS_PATH, 'pairs:', len(_qa_pairs))
    _qa_pairs[:2]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Acoustic Metrics

    Independently runnable from `audio.mp3`. If `report.roles.json` exists, candidate-only segment estimates are also included.
    """)
    return


@app.cell
def _(
    AUDIO_METRICS_PATH,
    AUDIO_PATH,
    Path,
    REPORT_ROLES_PATH,
    distribution,
    load_json,
    math,
    pct,
    save_json,
):
    def extract_audio_metrics(audio_path: Path, report_path: Path | None=None) -> dict:
        import torch
        import torchaudio
        waveform, sr = torchaudio.load(str(audio_path))
        mono = waveform.mean(dim=0)
        duration = mono.numel() / sr
        abs_x = mono.abs()
        rms = torch.sqrt(torch.mean(mono ** 2)).item()
        peak = abs_x.max().item()
        clipping_ratio = float((abs_x > 0.98).float().mean().item())
        frame = max(1, int(sr * 0.05))
        frames = mono[:mono.numel() // frame * frame].reshape(-1, frame) if mono.numel() >= frame else mono.reshape(1, -1)
        frame_rms = torch.sqrt(torch.mean(frames ** 2, dim=1)).numpy().tolist()
        noise_floor = pct(frame_rms, 10)
        signal_level = pct(frame_rms, 90)
        snr_db = 20 * math.log10((signal_level + 1e-09) / (noise_floor + 1e-09))
        silence_threshold = max(noise_floor * 1.8, rms * 0.18)
        silence_ratio = sum((1 for v in frame_rms if v < silence_threshold)) / max(1, len(frame_rms))
        candidate_segments = []
        if report_path and report_path.exists():
            _report = load_json(report_path)
            for turn in _report.get('turns', []):
                if turn['speaker'] != 'SPEAKER_01':
                    continue
                start_i = max(0, int(turn['start'] * sr))
                end_i = min(mono.numel(), int(turn['end'] * sr))
                seg = mono[start_i:end_i]
                if seg.numel() == 0:
                    continue
                seg_rms = torch.sqrt(torch.mean(seg ** 2)).item()
                candidate_segments.append({'turn_id': turn['id'], 'rms': round(seg_rms, 6), 'duration': turn['duration']})
        return {'source': 'audio', 'audio_file': str(audio_path), 'duration_seconds': round(duration, 2), 'sample_rate': sr, 'channels': int(waveform.shape[0]), 'rms': round(rms, 6), 'peak': round(peak, 6), 'clipping_ratio': round(clipping_ratio, 6), 'noise_floor_rms': round(noise_floor, 6), 'signal_level_rms': round(signal_level, 6), 'snr_db_estimate': round(snr_db, 2), 'silence_ratio_estimate': round(silence_ratio, 4), 'candidate_segments': candidate_segments, 'candidate_rms_distribution': distribution([s['rms'] for s in candidate_segments])}
    audio_metrics = extract_audio_metrics(AUDIO_PATH, REPORT_ROLES_PATH if REPORT_ROLES_PATH.exists() else None)
    save_json(AUDIO_METRICS_PATH, audio_metrics)
    print('Saved:', AUDIO_METRICS_PATH)
    audio_metrics
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6. Timing & Conversation Metrics

    Independently runnable from `report.roles.json`. Captures WPM, latency, pauses, fillers, repetitions, overlaps, rushing/dragging proxies, and conversation flow.
    """)
    return


@app.cell
def _(
    REPORT_PATH,
    REPORT_ROLES_PATH,
    TIMING_METRICS_PATH,
    distribution,
    load_json,
    re,
    save_json,
    statistics,
):
    FILLER_RE = re.compile('\\b(um+|uh+|erm+|hmm+|like|you know|basically|actually)\\b', re.I)

    def count_false_starts_and_repetition(text: str) -> dict:
        words = re.findall("[A-Za-z']+", text.lower())
        adjacent_repeats = sum((1 for a, b in zip(words, words[1:]) if a == b))
        repeated_bigrams = 0
        bigrams = list(zip(words, words[1:]))
        for a, b in zip(bigrams, bigrams[1:]):
            if a == b:
                repeated_bigrams += 1
        return {'adjacent_word_repeats': adjacent_repeats, 'repeated_bigrams': repeated_bigrams}

    def extract_timing_metrics(report: dict) -> dict:
        candidate_turns = [t for t in _report['turns'] if t['speaker'] == 'SPEAKER_01']
        latencies = [l for l in _report.get('latency', []) if l['to_speaker'] == 'SPEAKER_01']
        pauses = [p for p in _report.get('pauses', []) if p['speaker'] == 'SPEAKER_01']
        overlaps = [o for o in _report.get('overlaps', []) if 'SPEAKER_01' in (o['speaker_a'], o['speaker_b'])]
        per_turn = []
        for t in candidate_turns:
            mins = max(t['duration'], 0.01) / 60
            wpm = t['word_count'] / mins
            reps = count_false_starts_and_repetition(t['text'])
            fillers = len(FILLER_RE.findall(t['text']))
            per_turn.append({'turn_id': t['id'], 'duration': t['duration'], 'word_count': t['word_count'], 'wpm': round(wpm, 2), 'filler_count': fillers, **reps})
        wpms = [t['wpm'] for t in per_turn]
        return {'source': 'transcript_timing', 'candidate_turn_count': len(candidate_turns), 'per_turn': per_turn, 'wpm': distribution(wpms), 'latency': distribution([l['duration'] for l in latencies]), 'pauses': distribution([p['duration'] for p in pauses]), 'long_pause_count_2_5s': sum((1 for p in pauses if p['duration'] >= 2.5)), 'filler_count': sum((t['filler_count'] for t in per_turn)), 'adjacent_word_repeats': sum((t['adjacent_word_repeats'] for t in per_turn)), 'repeated_bigrams': sum((t['repeated_bigrams'] for t in per_turn)), 'overlap_count': len(overlaps), 'rushing_turns': [t for t in per_turn if t['wpm'] > 180], 'dragging_turns': [t for t in per_turn if t['wpm'] < 90 and t['word_count'] > 8], 'wpm_variance': round(statistics.pvariance(wpms), 2) if len(wpms) > 1 else 0}
    _report = load_json(REPORT_ROLES_PATH if REPORT_ROLES_PATH.exists() else REPORT_PATH)
    timing_metrics = extract_timing_metrics(_report)
    save_json(TIMING_METRICS_PATH, timing_metrics)
    print('Saved:', TIMING_METRICS_PATH)
    timing_metrics
    return (FILLER_RE,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7. Transcript/NLP Metrics

    Independently runnable from `report.roles.json`. Uses copied feature-extraction logic inspired by `analyze_nlp.py`.
    """)
    return


@app.cell
def _(
    FILLER_RE,
    NLP_METRICS_PATH,
    REPORT_PATH,
    REPORT_ROLES_PATH,
    load_json,
    re,
    save_json,
    statistics,
):
    CONNECTORS = {'however', 'therefore', 'although', 'despite', 'because', 'since', 'while', 'whereas', 'moreover', 'furthermore', 'instead', 'as', 'result', 'first', 'second', 'finally'}

    def tokenize_words(text: str) -> list[str]:
        return re.findall("[A-Za-z']+", text.lower())

    def extract_simple_nlp_features(text: str) -> dict:
        words = tokenize_words(text)
        sentences = [s.strip() for s in re.split('[.!?]+', text) if s.strip()]
        if not words:
            return {'word_count': 0}
        counts = {w: words.count(w) for w in set(words)}
        repeated_words = sum((c - 1 for c in counts.values() if c > 1))
        connector_count = sum((1 for w in words if w in CONNECTORS))
        filler_count = len(FILLER_RE.findall(text))
        sentence_lengths = [len(tokenize_words(s)) for s in sentences] or [len(words)]
        try:
            from wordfreq import zipf_frequency
            zipfs = [zipf_frequency(w, 'en') for w in words]
            avg_zipf = sum(zipfs) / len(zipfs)
            rare_ratio = sum((1 for z in zipfs if z < 4.0)) / len(zipfs)
        except Exception:
            avg_zipf = 0
            rare_ratio = 0
        return {'word_count': len(words), 'unique_word_count': len(set(words)), 'type_token_ratio': round(len(set(words)) / len(words), 4), 'repeated_word_count': repeated_words, 'connector_count': connector_count, 'filler_count': filler_count, 'sentence_count': len(sentences), 'avg_sentence_length': round(sum(sentence_lengths) / len(sentence_lengths), 2), 'sentence_length_variance': round(statistics.pvariance(sentence_lengths), 2) if len(sentence_lengths) > 1 else 0, 'long_word_ratio': round(sum((1 for w in words if len(w) > 6)) / len(words), 4), 'avg_zipf': round(avg_zipf, 4), 'rare_word_ratio': round(rare_ratio, 4)}

    def extract_candidate_nlp_metrics(report: dict) -> dict:
        candidate_turns = [t for t in _report['turns'] if t['speaker'] == 'SPEAKER_01']
        turns = []
        for t in candidate_turns:
            turns.append({'turn_id': t['id'], 'text': t['text'], **extract_simple_nlp_features(t['text'])})
        all_text = ' '.join((t['text'] for t in candidate_turns))
        return {'source': 'transcript_nlp', 'turns': turns, 'overall': extract_simple_nlp_features(all_text)}
    _report = load_json(REPORT_ROLES_PATH if REPORT_ROLES_PATH.exists() else REPORT_PATH)
    nlp_metrics = extract_candidate_nlp_metrics(_report)
    save_json(NLP_METRICS_PATH, nlp_metrics)
    print('Saved:', NLP_METRICS_PATH)
    nlp_metrics['overall']
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8. Semantic LLM Rubric Scoring

    Independently runnable from `qa_pairs.json`. This captures rubric elements that require interpretation of question-answer meaning.
    """)
    return


@app.cell
def _(
    FORCE_LLM,
    QA_PAIRS_PATH,
    SEMANTIC_SCORES_PATH,
    get_openrouter_client,
    llm_json_call,
    load_json,
    save_json,
):
    SEMANTIC_SIGNAL_CODES = ['Rel', 'Drf', 'Ex', 'Ctx', 'Act', 'Res', 'STAR', 'Det', 'Num', 'Nam', 'Step', 'Ver', 'Con', 'Why', 'Opt', 'Jud', 'C&E', 'Ref', 'Ins', 'Beyond', 'Own', 'Imp', 'Comp', 'Prof', 'Coll', 'Lead', 'Prob', 'Learn', 'Trust', 'Pres']

    def semantic_schema() -> dict:
        score_obj = {'type': 'object', 'properties': {'score': {'type': 'integer'}, 'confidence': {'type': 'number'}, 'evidence': {'type': 'string'}}, 'required': ['score', 'confidence', 'evidence'], 'additionalProperties': False}
        return {'type': 'object', 'properties': {'answer_turn_id': {'type': 'integer'}, 'summary': {'type': 'string'}, 'scores': {'type': 'object', 'properties': {code: score_obj for code in SEMANTIC_SIGNAL_CODES}, 'required': SEMANTIC_SIGNAL_CODES, 'additionalProperties': False}}, 'required': ['answer_turn_id', 'summary', 'scores'], 'additionalProperties': False}

    def score_one_answer_semantically(pair: dict, model: str='openai/gpt-4o-mini') -> dict:
        client = get_openrouter_client()
        system = 'You are an interview-rubric evaluator. Score only what is evidenced in the answer. Use 0-4 integers. Return only JSON.'
        rubric = '\n'.join(['Rel relevance/on target', 'Drf no drift', 'Ex best example', 'Ctx named context', 'Act candidate action', 'Res result', 'STAR full answer arc', 'Det detail', 'Num numbers/facts', 'Nam names/entities', 'Step step by step', 'Ver verifiable', 'Con concrete language', 'Why reasoning', 'Opt options weighed', 'Jud judgment shown', 'C&E cause/effect', 'Ref reflection', 'Ins insight', 'Beyond goes beyond direct ask', 'Own ownership', 'Imp impact', 'Comp role competency', 'Prof professional maturity', 'Coll collaboration', 'Lead leadership', 'Prob problem solving', 'Learn learnability', 'Trust listener trust', 'Pres presence impression from text only'])
        user = f"Question:\n{pair['question']}\n\nCandidate answer:\n{pair['answer']}\n\nScore each signal from 0 to 4. Use evidence from the answer. If not demonstrated, score 0.\n\nSignals:\n{rubric}"
        result = llm_json_call(client, model, system, user, semantic_schema(), 'SemanticRubricScore')
        result['answer_turn_id'] = pair['answer_turn_id']
        return result
    _qa_pairs = load_json(QA_PAIRS_PATH)
    if SEMANTIC_SCORES_PATH.exists() and (not FORCE_LLM):
        semantic_scores = load_json(SEMANTIC_SCORES_PATH)
        print('Reusing:', SEMANTIC_SCORES_PATH)
    else:
        semantic_scores = []
        for pair in _qa_pairs:
            if pair['word_count'] < 3:
                continue
            print('Scoring answer turn', pair['answer_turn_id'])
            semantic_scores.append(score_one_answer_semantically(pair))
        save_json(SEMANTIC_SCORES_PATH, semantic_scores)
    print('Saved:', SEMANTIC_SCORES_PATH, 'answers:', len(semantic_scores))
    semantic_scores[:1]
    return (SEMANTIC_SIGNAL_CODES,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 9. Derived & Composite Signal Report

    Independently runnable after metrics files exist. Combines acoustic, timing, NLP, and LLM semantic evidence into one `signal_report.json`.
    """)
    return


@app.cell
def _(
    AUDIO_METRICS_PATH,
    AUDIO_PATH,
    NLP_METRICS_PATH,
    SEMANTIC_SCORES_PATH,
    SEMANTIC_SIGNAL_CODES,
    SIGNAL_REPORT_PATH,
    TIMING_METRICS_PATH,
    load_json,
    save_json,
    time,
):
    def clamp_score(x: float) -> int:
        return int(max(0, min(4, round(x))))

    def band_score(value: float, bands: list[tuple[float, int]]) -> int:
        for threshold, score in bands:
            if value <= threshold:
                return score
        return bands[-1][1]

    def avg_score(*vals: float) -> int:
        present = [v for v in vals if v is not None]
        return clamp_score(sum(present) / len(present)) if present else 0

    def semantic_average(semantic_scores: list[dict], code: str) -> dict:
        vals = []
        evidence = []
        conf = []
        for item in semantic_scores:
            s = item.get('scores', {}).get(code)
            if s:
                vals.append(s['score'])
                conf.append(s.get('confidence', 0.7))
                if s.get('evidence'):
                    evidence.append(f"turn {item['answer_turn_id']}: {s['evidence']}")
        return {'score': avg_score(*vals) if vals else 0, 'confidence': round(sum(conf) / len(conf), 2) if conf else 0.0, 'evidence': evidence[:5]}

    def make_signal(code, name, category, layer, source, score, confidence=0.7, raw=None, depends_on=None, evidence=None):
        return {'code': code, 'name': name, 'category': category, 'layer': layer, 'source': source, 'score': int(score), 'confidence': confidence, 'raw': raw or {}, 'depends_on': depends_on or [], 'evidence': evidence or []}

    audio = load_json(AUDIO_METRICS_PATH) if AUDIO_METRICS_PATH.exists() else {}
    timing = load_json(TIMING_METRICS_PATH) if TIMING_METRICS_PATH.exists() else {}
    nlp = load_json(NLP_METRICS_PATH) if NLP_METRICS_PATH.exists() else {}
    semantic = load_json(SEMANTIC_SCORES_PATH) if SEMANTIC_SCORES_PATH.exists() else []
    signals = {}

    mean_wpm = timing.get('wpm', {}).get('mean', 0)
    wpm_score = 4 if 120 <= mean_wpm <= 145 else 3 if 100 <= mean_wpm <= 160 else 2 if 90 <= mean_wpm <= 180 else 1 if mean_wpm else 0
    signals['WPM'] = make_signal('WPM', 'Words/min', 'Pace & Rhythm', 'M', 'transcript_timing', wpm_score, 0.9, {'mean_wpm': mean_wpm})
    signals['Lat'] = make_signal('Lat', 'Latency', 'Pauses & Silence', 'M', 'transcript_timing', 4 if 2 <= timing.get('latency', {}).get('median', 0) <= 5 else 2, 0.85, timing.get('latency', {}))
    signals['FP'] = make_signal('FP', 'Filled pause', 'Pauses & Silence', 'M', 'transcript', 4 if timing.get('filler_count', 0) <= 1 else 3 if timing.get('filler_count', 0) <= 4 else 2 if timing.get('filler_count', 0) <= 8 else 1, 0.75, {'count': timing.get('filler_count', 0)})
    signals['Sil'] = make_signal('Sil', 'Long silence', 'Pauses & Silence', 'M', 'transcript_timing', 4 if timing.get('long_pause_count_2_5s', 0) == 0 else 3 if timing.get('long_pause_count_2_5s', 0) <= 1 else 2 if timing.get('long_pause_count_2_5s', 0) <= 3 else 1, 0.75, {'count_2_5s': timing.get('long_pause_count_2_5s', 0)})
    signals['Rep'] = make_signal('Rep', 'Repetition', 'Fluency', 'M', 'transcript', 4 if timing.get('adjacent_word_repeats', 0) == 0 else 3 if timing.get('adjacent_word_repeats', 0) <= 2 else 2 if timing.get('adjacent_word_repeats', 0) <= 6 else 1, 0.8, {'adjacent_word_repeats': timing.get('adjacent_word_repeats', 0)})
    signals['Vol'] = make_signal('Vol', 'Volume', 'Voice Delivery', 'M', 'audio', 3 if audio.get('rms', 0) > 0.005 else 1, 0.55, {'rms': audio.get('rms')})
    signals['SNR'] = make_signal('SNR', 'SNR', 'Recording Quality', 'M', 'audio', 4 if audio.get('snr_db_estimate', 0) >= 20 else 3 if audio.get('snr_db_estimate', 0) >= 12 else 2 if audio.get('snr_db_estimate', 0) >= 6 else 1, 0.65, {'snr_db_estimate': audio.get('snr_db_estimate')})
    signals['Clip'] = make_signal('Clip', 'Clipping', 'Recording Quality', 'M', 'audio', 4 if audio.get('clipping_ratio', 1) < 0.001 else 2, 0.8, {'clipping_ratio': audio.get('clipping_ratio')})
    signals['Noi'] = make_signal('Noi', 'Noise', 'Recording Quality', 'M', 'audio', signals['SNR']['score'], 0.55, {'noise_floor_rms': audio.get('noise_floor_rms')})
    overall_nlp = nlp.get('overall', {})
    signals['Voc'] = make_signal('Voc', 'Vocabulary', 'Language Quality', 'J', 'transcript_nlp', 3 if overall_nlp.get('type_token_ratio', 0) > 0.55 else 2 if overall_nlp.get('type_token_ratio', 0) > 0.42 else 1, 0.65, overall_nlp)
    signals['RepW'] = make_signal('RepW', 'Word repeat', 'Language Quality', 'M', 'transcript_nlp', 4 if overall_nlp.get('repeated_word_count', 0) < 8 else 3 if overall_nlp.get('repeated_word_count', 0) < 18 else 2 if overall_nlp.get('repeated_word_count', 0) < 35 else 1, 0.75, {'repeated_word_count': overall_nlp.get('repeated_word_count', 0)})
    signals['Conn'] = make_signal('Conn', 'Connectors', 'Fluency', 'J', 'transcript_nlp', 4 if overall_nlp.get('connector_count', 0) >= 8 else 3 if overall_nlp.get('connector_count', 0) >= 5 else 2 if overall_nlp.get('connector_count', 0) >= 2 else 1, 0.65, {'connector_count': overall_nlp.get('connector_count', 0)})

    for code in SEMANTIC_SIGNAL_CODES:
        sem = semantic_average(semantic, code)
        if code not in signals:
            signals[code] = make_signal(code, code, 'Semantic/Rubric', 'J', 'llm_semantic', sem['score'], sem['confidence'], evidence=sem['evidence'])

    signals['Pac'] = make_signal('Pac', 'Pace control', 'Pace & Rhythm', 'D', 'derived', avg_score(signals['WPM']['score'], 4 - min(4, len(timing.get('rushing_turns', []))), 4 - min(4, len(timing.get('dragging_turns', [])))), 0.75, depends_on=['WPM','Rus','Drg','Acc','Dec'])
    signals['Pau'] = make_signal('Pau', 'Pause quality', 'Pauses & Silence', 'D', 'derived', avg_score(signals['Lat']['score'], signals['Sil']['score'], signals['FP']['score']), 0.72, depends_on=['Lat','Sil','FP','HP','OP','RP'])
    signals['Flo'] = make_signal('Flo', 'Speech flow', 'Fluency', 'D', 'derived', avg_score(signals['Rep']['score'], signals['FP']['score'], signals['Pau']['score']), 0.72, depends_on=['Rep','FP','Pau','FS','Frag','Run'])
    signals['Trust'] = make_signal('Trust', 'Trust', 'Confidence Signals', 'J', 'llm_semantic+derived', avg_score(signals.get('Trust', {}).get('score', 0), signals.get('Rel', {}).get('score', 0), signals.get('Own', {}).get('score', 0), signals.get('Imp', {}).get('score', 0)), 0.72, depends_on=['Rel','Own','Imp','Det'])
    signals['Conf'] = make_signal('Conf', 'Confidence', 'Confidence Signals', 'C', 'derived', avg_score(signals['Vol']['score'], signals['Pac']['score'], signals['Pau']['score'], signals.get('Pres', {}).get('score', 0)), 0.65, depends_on=['Vol','Pac','Pau','Pres'])

    signal_report = {'audio_file': str(AUDIO_PATH), 'created_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'signals': signals, 'artifacts': {'audio_metrics': str(AUDIO_METRICS_PATH), 'timing_metrics': str(TIMING_METRICS_PATH), 'nlp_metrics': str(NLP_METRICS_PATH), 'semantic_scores': str(SEMANTIC_SCORES_PATH)}}
    save_json(SIGNAL_REPORT_PATH, signal_report)
    print('Saved:', SIGNAL_REPORT_PATH, 'signals:', len(signals))
    list(signals.items())[:5]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 10. Review Tables
    """)
    return


@app.cell
def _(SIGNAL_REPORT_PATH, display, load_json):
    _report = load_json(SIGNAL_REPORT_PATH)
    rows = sorted(_report['signals'].values(), key=lambda s: (s['category'], s['code']))
    try:
        import pandas as pd
        display(pd.DataFrame([{k: s.get(k) for k in ['code', 'name', 'category', 'layer', 'source', 'score', 'confidence']} for s in rows]))
    except Exception:
        for s in rows:
            print(f"{s['code']:>6} | {s['score']} | {s['layer']} | {s['source']} | {s['name']}")
    return


if __name__ == "__main__":
    app.run()

