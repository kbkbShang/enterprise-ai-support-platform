import os
import time
import logging
from typing import Any
import threading
import json
from pydantic import BaseModel, ValidationError

from google import genai


logger = logging.getLogger("llm_gateway")

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MAX_LLM_CALLS_PER_SECOND = int(os.getenv("MAX_LLM_CALLS_PER_SECOND", "2"))

_rate_limit_lock = threading.Lock()
_last_call_timestamps = []

client = genai.Client(api_key=GEMINI_API_KEY)

def _apply_rate_limit():
    global _last_call_timestamps

    while True:
        with _rate_limit_lock:
            now = time.time()

            _last_call_timestamps = [
                ts for ts in _last_call_timestamps
                if now - ts < 1.0
            ]

            if len(_last_call_timestamps) < MAX_LLM_CALLS_PER_SECOND:
                _last_call_timestamps.append(now)
                return

        time.sleep(0.05)


def generate_content(
    contents: Any,
    config: Any = None,
    model: str | None = None,
    max_retries: int = 2,
) -> Any:
    selected_model = model or DEFAULT_MODEL
    model_candidates = [selected_model]

    if FALLBACK_MODEL and FALLBACK_MODEL != selected_model:
        model_candidates.append(FALLBACK_MODEL)

    last_error = None

    for current_model in model_candidates:
        for attempt in range(1, max_retries + 1):
            start_time = time.time()

            try:
                _apply_rate_limit()

                response = client.models.generate_content(
                    model=current_model,
                    contents=contents,
                    config=config,
                )

                latency_ms = int((time.time() - start_time) * 1000)

                usage = getattr(response, "usage_metadata", None)

                logger.info(
                    {
                        "event": "llm_call_success",
                        "model": current_model,
                        "primary_model": selected_model,
                        "fallback_used": current_model != selected_model,
                        "attempt": attempt,
                        "latency_ms": latency_ms,
                        "input_tokens": getattr(usage, "prompt_token_count", None),
                        "output_tokens": getattr(usage, "candidates_token_count", None),
                        "total_tokens": getattr(usage, "total_token_count", None),
                    }
                )       

                return response

            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                last_error = e

                logger.warning(
                    {
                        "event": "llm_call_failed",
                        "model": current_model,
                        "primary_model": selected_model,
                        "fallback_used": current_model != selected_model,
                        "attempt": attempt,
                        "latency_ms": latency_ms,
                        "error": str(e),
                    }
                )

                if attempt < max_retries:
                    time.sleep(2 ** attempt)

        logger.warning(
            {
                "event": "llm_model_exhausted",
                "model": current_model,
                "error": str(last_error),
            }
        )

    raise RuntimeError(
        f"LLM call failed for all models after retries: {last_error}"
    )

def extract_json_text(text: str) -> str:
    text = text.strip()

    if "```json" in text:
        start = text.find("```json") + len("```json")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + len("```")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start:end + 1].strip()

    return text

def generate_structured_content(
    contents: Any,
    schema: type[BaseModel],
    config: Any = None,
    model: str | None = None,
    max_retries: int = 2,
) -> BaseModel:
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = generate_content(
                contents=contents,
                config=config,
                model=model,
                max_retries=1,
            )

            text = response.text or ""
            json_text = extract_json_text(text)
            parsed = json.loads(json_text)

            validated = schema.model_validate(parsed)

            logger.info(
                {
                    "event": "llm_structured_validation_success",
                    "schema": schema.__name__,
                    "attempt": attempt,
                }
            )

            return validated, response

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e

            logger.warning(
                {
                    "event": "llm_structured_validation_failed",
                    "schema": schema.__name__,
                    "attempt": attempt,
                    "error": str(e),
                }
            )

            if attempt < max_retries:
                time.sleep(2 ** attempt)

    raise RuntimeError(
        f"Structured LLM response validation failed after {max_retries} attempts: {last_error}"
    )