import os
import time
import logging
from typing import Any

from google import genai


logger = logging.getLogger("llm_gateway")

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


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
                response = client.models.generate_content(
                    model=current_model,
                    contents=contents,
                    config=config,
                )

                latency_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    {
                        "event": "llm_call_success",
                        "model": current_model,
                        "primary_model": selected_model,
                        "fallback_used": current_model != selected_model,
                        "attempt": attempt,
                        "latency_ms": latency_ms,
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