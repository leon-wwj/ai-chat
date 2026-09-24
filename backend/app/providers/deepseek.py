import asyncio
import json
import time

import httpx

from app.config import RETRY_BACKOFF_SECONDS, RETRY_MAX_ATTEMPTS, RETRYABLE_STATUS
from app.logging_setup import logger


def backoff_seconds(attempt: int) -> float:
    """Exponential backoff: 0.5s, 1s, 2s ..."""
    return RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))


async def request_with_retry(
    rid: str,
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict,
    json_body: dict | None = None,
):
    """Send one HTTP request, retrying transport errors / 429 / 5xx with backoff.

    Returns (response, error_message). `response` is None only when every attempt
    failed at the transport level, and `error_message` then holds the last error.
    A returned non-200 response means the status was not worth retrying, or the
    retries ran out - the caller reports the real status in either case.
    """
    last_error = None

    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            resp = await client.request(method, url, headers=headers, json=json_body)
        except httpx.HTTPError as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "req=%s upstream %s transport error attempt=%d/%d error=%s",
                rid, method, attempt, RETRY_MAX_ATTEMPTS, exc,
            )
            if attempt == RETRY_MAX_ATTEMPTS:
                break
        else:
            if resp.status_code not in RETRYABLE_STATUS:
                if attempt > 1:
                    logger.info(
                        "req=%s upstream %s recovered on attempt=%d status=%d",
                        rid, method, attempt, resp.status_code,
                    )
                return resp, None

            last_error = f"HTTP {resp.status_code}"
            logger.warning(
                "req=%s upstream %s retryable status=%d attempt=%d/%d",
                rid, method, resp.status_code, attempt, RETRY_MAX_ATTEMPTS,
            )
            if attempt == RETRY_MAX_ATTEMPTS:
                return resp, None

        delay = backoff_seconds(attempt)
        logger.info(
            "req=%s %s retrying in %.1fs (next attempt %d/%d)",
            rid, method, delay, attempt + 1, RETRY_MAX_ATTEMPTS,
        )
        await asyncio.sleep(delay)

    return None, last_error


async def stream_llm(rid: str, url: str, headers: dict, payload: dict):
    """Stream an OpenAI-compatible SSE response.

    Only the connection is retried, and only while nothing has been sent to the
    client yet - retrying after partial content would duplicate the answer.
    """
    model_sent = False
    content_started = False
    started = time.perf_counter()

    logger.info("req=%s stream start", rid)

    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        body = (await resp.aread()).decode("utf-8", errors="replace")
                        if resp.status_code in RETRYABLE_STATUS and attempt < RETRY_MAX_ATTEMPTS:
                            logger.warning(
                                "req=%s stream upstream status=%d attempt=%d/%d, will retry",
                                rid, resp.status_code, attempt, RETRY_MAX_ATTEMPTS,
                            )
                            await asyncio.sleep(backoff_seconds(attempt))
                            continue
                        logger.error(
                            "req=%s stream upstream status=%d elapsed=%.0fms body=%s",
                            rid, resp.status_code,
                            (time.perf_counter() - started) * 1000, body[:200],
                        )
                        yield f"__ERROR__:LLM 接口返回 {resp.status_code}: {body[:500]}"
                        return

                    logger.info("req=%s stream connected attempt=%d", rid, attempt)

                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            real_model = obj.get("model")
                            if real_model and not model_sent:
                                model_sent = True
                                yield f"__MODEL__:{real_model}\n"
                            content = obj["choices"][0]["delta"].get("content")
                            if content:
                                content_started = True
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

                    logger.info(
                        "req=%s stream done elapsed=%.0fms",
                        rid, (time.perf_counter() - started) * 1000,
                    )
                    return
        except httpx.HTTPError as exc:
            if not content_started and attempt < RETRY_MAX_ATTEMPTS:
                logger.warning(
                    "req=%s stream connect error attempt=%d/%d error=%s, will retry",
                    rid, attempt, RETRY_MAX_ATTEMPTS, exc,
                )
                await asyncio.sleep(backoff_seconds(attempt))
                continue
            logger.error(
                "req=%s stream failed attempt=%d elapsed=%.0fms error=%s",
                rid, attempt, (time.perf_counter() - started) * 1000, exc,
            )
            yield f"__ERROR__:连接 LLM 服务失败: {exc}"
            return
