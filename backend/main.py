from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@app.post("/chat")
async def chat(req: ChatRequest):
    """转发到 OpenAI 兼容的 LLM 接口（DeepSeek / OpenAI / Kimi 等）。

    API Key 由前端（用户浏览器）传入，后端仅中转，不落盘。
    """
    url = f"{req.base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {req.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
        "stream": False,
    }

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
