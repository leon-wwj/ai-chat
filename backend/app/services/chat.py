"""聊天业务：组装上游请求、调用上游、解析响应。

不碰 FastAPI 的 Response 类型，也不决定 HTTP 状态码——那是 routers 的职责。
成功返回业务结果，失败返回 (None, 错误描述)。
"""

import asyncio
import time
from dataclasses import dataclass

import httpx

from app.config import TIMEOUT_SECONDS
from app.db.database import SessionLocal
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
from app.services import conversation


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


async def _persist(
    rid: str,
    conversation_id: int,
    role: str,
    content: str,
    model: str | None,
    status: str,
) -> None:
    """落库是副作用，失败只记日志——不能因为存不下就把已经发出的内容毁掉。"""
    try:
        async with SessionLocal() as session:
            await conversation.add_message(
                session, conversation_id, role, content, model, status
            )
    except Exception as exc:
        logger.error("req=%s persist failed role=%s error=%r", rid, role, exc)


async def stream_chat(rid: str, req: ChatRequest):
    """流式转发，并按 req.conversation_id 落库。

    客户端点"停止"时后端不一定立刻知道（要等写入失败或连接被检测到断开），
    所以助手回复的落库放在生成器收尾处：正常结束 = complete，
    被取消/关闭 = interrupted（保留已经生成的部分），上游报错 = error。
    """
    url = chat_completions_url(req.base_url)
    headers = auth_headers(req.api_key)
    payload = build_chat_payload(
        req.model, [m.model_dump() for m in req.messages], stream=True
    )

    collected: list[str] = []
    real_model: str | None = None
    status = "complete"

    if req.conversation_id:
        # 本轮新增的用户输入 = 最后一条 user 消息
        last_user = next(
            (m for m in reversed(req.messages) if m.role == "user"), None
        )
        if last_user:
            await _persist(
                rid, req.conversation_id, "user", last_user.content, None, "complete"
            )

    try:
        async for chunk in stream_llm(rid, url, headers, payload):
            if chunk.startswith("__MODEL__:"):
                real_model = chunk[len("__MODEL__:"):].strip()
            elif chunk.startswith("__ERROR__:"):
                status = "error"
            else:
                collected.append(chunk)
            yield chunk
    except (asyncio.CancelledError, GeneratorExit):
        status = "interrupted"
        raise
    finally:
        if req.conversation_id and collected:
            await _persist(
                rid,
                req.conversation_id,
                "assistant",
                "".join(collected),
                real_model,
                status,
            )


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
