"""LLM client abstraction: Google GenAI for file-based calls, OpenRouter for text-only."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import openai
from google import genai
from google.genai import types


_client_cache: dict[str, Any] = {}


def get_google_client():
    if "google" not in _client_cache:
        _client_cache["google"] = genai.Client()
    return _client_cache["google"]


def get_openrouter_client():
    if "openrouter" not in _client_cache:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        _client_cache["openrouter"] = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client_cache["openrouter"]


def upload_file_to_google(file_path: Path) -> str:
    """Upload a file to Google GenAI Files API. Returns the file name for inline use."""
    client = get_google_client()
    uploaded = client.files.upload(file=file_path)
    return uploaded.name


def upload_audio_for_scoring(audio_path: Path) -> Any:
    """Upload audio file once for reuse across multiple audio-scoring elements."""
    client = get_google_client()
    return client.files.upload(file=str(audio_path))


def cleanup_uploaded_file(file_obj: Any) -> None:
    """Delete uploaded file after all scoring is done. Best-effort."""
    try:
        client = get_google_client()
        client.files.delete(name=file_obj.name)
    except Exception:
        pass


def llm_call(text: str, system: str = "", model: str = "anthropic/claude-sonnet-4", temperature: float = 0.0) -> str:
    """Text-only LLM call via OpenRouter."""
    client = get_openrouter_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": text})
    resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
    return resp.choices[0].message.content or ""


def llm_call_with_audio(
    audio_path: Path,
    prompt: str,
    system: str = "",
    model: str = "google/gemini-2.5-flash",
    uploaded_file: Any | None = None,
) -> str:
    """LLM call with audio file via Google GenAI Files API.

    Args:
        audio_path: Path to audio file (used only if uploaded_file is None).
        prompt: The user prompt text.
        system: System instruction for the model.
        model: Google GenAI model identifier.
        uploaded_file: Pre-uploaded file object from upload_audio_for_scoring().
            If provided, skips re-uploading. If None, uploads audio_path.
    """
    client = get_google_client()

    if uploaded_file is None:
        uploaded_file = client.files.upload(file=str(audio_path))

    contents = [uploaded_file, prompt]

    config_kwargs: dict[str, Any] = {}
    if system:
        config_kwargs["system_instruction"] = system
    config_kwargs["response_mime_type"] = "application/json"

    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    return resp.text or ""


def llm_json(text: str, system: str = "", model: str = "anthropic/claude-sonnet-4", temperature: float = 0.0) -> dict:
    """LLM call that returns parsed JSON."""
    raw = llm_call(text, system=system, model=model, temperature=temperature)
    # Strip markdown fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    return json.loads(raw)
