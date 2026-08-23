import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
TIMEOUT_SECONDS = 60


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    stream: bool = False


@app.post("/chat")
async def chat(req: ChatRequest):
    url = f"{req.base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {req.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
    }

    if req.stream:
        payload["stream"] = True
        return StreamingResponse(
            stream_llm(url, headers, payload),
            media_type="text/plain",
        )

    payload["stream"] = False

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        return JSONResponse(
            status_code=502,
            content={"error": f"连接 LLM 服务失败: {exc}"},
        )

    if resp.status_code != 200:
        return JSONResponse(
            status_code=502,
            content={"error": f"LLM 接口返回 {resp.status_code}: {resp.text[:500]}"},
        )

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        return JSONResponse(
            status_code=502,
            content={"error": f"LLM 响应格式异常: {exc}"},
        )

    return {
        "role": "assistant",
        "content": content,
    }


async def stream_llm(url: str, headers: dict, payload: dict):
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")
                    yield f"__ERROR__:LLM 接口返回 {resp.status_code}: {body[:500]}"
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        content = obj["choices"][0]["delta"].get("content")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except httpx.HTTPError as exc:
        yield f"__ERROR__:连接 LLM 服务失败: {exc}"
