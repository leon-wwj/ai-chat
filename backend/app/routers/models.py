import time

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import TIMEOUT_SECONDS
from app.logging_setup import logger
from app.providers.deepseek import request_with_retry
from app.schemas import ModelsRequest
from app.utils import new_request_id

router = APIRouter()


@router.post("/models")
async def list_models(req: ModelsRequest):
    rid = new_request_id()
    url = f"{req.base_url.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {req.api_key}"}

    logger.info("req=%s /models start base_url=%s", rid, req.base_url)

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        resp, error = await request_with_retry(rid, client, "GET", url, headers)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if resp is None:
        logger.error(
            "req=%s /models upstream unreachable elapsed=%.0fms error=%s",
            rid, elapsed_ms, error,
        )
        return JSONResponse(
            status_code=502,
            content={"error": f"连接模型列表服务失败: {error}"},
        )

    if resp.status_code != 200:
        logger.error(
            "req=%s /models upstream status=%d elapsed=%.0fms body=%s",
            rid, resp.status_code, elapsed_ms, resp.text[:200],
        )
        return JSONResponse(
            status_code=502,
            content={"error": f"模型列表接口返回 {resp.status_code}: {resp.text[:500]}"},
        )

    try:
        data = resp.json()
        models = [item["id"] for item in data["data"]]
    except (KeyError, TypeError, ValueError) as exc:
        logger.error(
            "req=%s /models malformed response elapsed=%.0fms error=%r",
            rid, elapsed_ms, exc,
        )
        return JSONResponse(
            status_code=502,
            content={"error": f"模型列表格式异常: {exc}"},
        )

    logger.info("req=%s /models ok count=%d elapsed=%.0fms", rid, len(models), elapsed_ms)

    return {"models": models}
