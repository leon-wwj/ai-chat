from pydantic import BaseModel

from app.config import DEFAULT_BASE_URL, DEFAULT_MODEL


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    stream: bool = False


class ModelsRequest(BaseModel):
    api_key: str
    base_url: str = DEFAULT_BASE_URL
