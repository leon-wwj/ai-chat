"""聊天业务：组装上游请求、调用上游、解析响应。

不碰 FastAPI 的 Response 类型，也不决定 HTTP 状态码——那是 routers 的职责。
成功返回业务结果，失败返回 (None, 错误描述)。
"""

import time
from dataclasses import dataclass

import httpx

from app.config import TIMEOUT_SECONDS
from app.logging_setup import logger
from app.providers.deepseek import (
    auth_headers,
    build_chat_payload,
    chat_completions_url,
    models_url,
    request_with_retry,
    stream_llm,
)
from app.schemas import ChatRequest, ModelsRequest


@dataclass
class ChatCompletion:
    content: str
    model: str


async def complete_chat(
    rid: str,
    req: ChatRequest,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[ChatCompletion | None, str | None]:
    url = chat_completions_url(req.base_url)
    headers = auth_headers(req.api_key)
    payload = build_chat_payload(
        req.model, [m.model_dump() for m in req.messages], stream=False
    )

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=transport) as client:
        resp, error = await request_with_retry(rid, client, "POST", url, headers, payload)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if resp is None:
        logger.error(
            "req=%s /chat upstream unreachable elapsed=%.0fms error=%s",
            rid, elapsed_ms, error,
        )
        return None, f"连接 LLM 服务失败: {error}"

    if resp.status_code != 200:
        logger.error(
            "req=%s /chat upstream status=%d elapsed=%.0fms body=%s",
            rid, resp.status_code, elapsed_ms, resp.text[:200],
        )
        return None, f"LLM 接口返回 {resp.status_code}: {resp.text[:500]}"

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.error(
            "req=%s /chat malformed response elapsed=%.0fms error=%r",
            rid, elapsed_ms, exc,
        )
        return None, f"LLM 响应格式异常: {exc}"

    model = data.get("model") or req.model
    content_len = len(content) if isinstance(content, str) else 0
    logger.info(
        "req=%s /chat ok model=%s chars=%d elapsed=%.0fms",
        rid, model, content_len, elapsed_ms,
    )
    return ChatCompletion(content=content, model=model), None


async def stream_chat(rid: str, req: ChatRequest):
    url = chat_completions_url(req.base_url)
    headers = auth_headers(req.api_key)
    payload = build_chat_payload(
        req.model, [m.model_dump() for m in req.messages], stream=True
    )

    async for chunk in stream_llm(rid, url, headers, payload):
        yield chunk


async def list_models(
    rid: str,
    req: ModelsRequest,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[list[str] | None, str | None]:
    url = models_url(req.base_url)
    headers = {"Authorization": f"Bearer {req.api_key}"}

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=transport) as client:
        resp, error = await request_with_retry(rid, client, "GET", url, headers)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if resp is None:
        logger.error(
            "req=%s /models upstream unreachable elapsed=%.0fms error=%s",
            rid, elapsed_ms, error,
        )
        return None, f"连接模型列表服务失败: {error}"

    if resp.status_code != 200:
        logger.error(
            "req=%s /models upstream status=%d elapsed=%.0fms body=%s",
            rid, resp.status_code, elapsed_ms, resp.text[:200],
        )
        return None, f"模型列表接口返回 {resp.status_code}: {resp.text[:500]}"

    try:
        data = resp.json()
        models = [item["id"] for item in data["data"]]
    except (KeyError, TypeError, ValueError) as exc:
        logger.error(
            "req=%s /models malformed response elapsed=%.0fms error=%r",
            rid, elapsed_ms, exc,
        )
        return None, f"模型列表格式异常: {exc}"

    logger.info("req=%s /models ok count=%d elapsed=%.0fms", rid, len(models), elapsed_ms)
    return models, None
