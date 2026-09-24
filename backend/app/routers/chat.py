import time

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import TIMEOUT_SECONDS
from app.logging_setup import logger
from app.providers.deepseek import request_with_retry, stream_llm
from app.schemas import ChatRequest
from app.utils import new_request_id

router = APIRouter()


@router.post("/chat")
async def chat(req: ChatRequest):
    rid = new_request_id()
    url = f"{req.base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {req.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
    }

    logger.info(
        "req=%s /chat start base_url=%s model=%s stream=%s messages=%d",
        rid, req.base_url, req.model, req.stream, len(req.messages),
    )

    if req.stream:
        payload["stream"] = True
        return StreamingResponse(
            stream_llm(rid, url, headers, payload),
            media_type="text/plain",
        )

    payload["stream"] = False

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        resp, error = await request_with_retry(rid, client, "POST", url, headers, payload)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if resp is None:
        logger.error(
            "req=%s /chat upstream unreachable elapsed=%.0fms error=%s",
            rid, elapsed_ms, error,
        )
        return JSONResponse(
            status_code=502,
            content={"error": f"连接 LLM 服务失败: {error}"},
        )

    if resp.status_code != 200:
        logger.error(
            "req=%s /chat upstream status=%d elapsed=%.0fms body=%s",
            rid, resp.status_code, elapsed_ms, resp.text[:200],
        )
        return JSONResponse(
            status_code=502,
            content={"error": f"LLM 接口返回 {resp.status_code}: {resp.text[:500]}"},
        )

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.error(
            "req=%s /chat malformed response elapsed=%.0fms error=%r",
            rid, elapsed_ms, exc,
        )
        return JSONResponse(
            status_code=502,
            content={"error": f"LLM 响应格式异常: {exc}"},
        )

    content_len = len(content) if isinstance(content, str) else 0
    logger.info(
        "req=%s /chat ok model=%s chars=%d elapsed=%.0fms",
        rid, data.get("model") or req.model, content_len, elapsed_ms,
    )

    return {
        "role": "assistant",
        "content": content,
        "model": data.get("model") or req.model,
    }
