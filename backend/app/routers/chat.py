from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.logging_setup import logger
from app.schemas import ChatRequest
from app.services.chat import complete_chat, stream_chat
from app.utils import new_request_id

router = APIRouter()


@router.post("/chat")
async def chat(req: ChatRequest):
    rid = new_request_id()

    logger.info(
        "req=%s /chat start base_url=%s model=%s stream=%s messages=%d",
        rid, req.base_url, req.model, req.stream, len(req.messages),
    )

    if req.stream:
        return StreamingResponse(stream_chat(rid, req), media_type="text/plain")

    result, error = await complete_chat(rid, req)
    if error is not None:
        return JSONResponse(status_code=502, content={"error": error})

    return {
        "role": "assistant",
        "content": result.content,
        "model": result.model,
    }
