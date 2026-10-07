from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
    # 带会话 id 时，本轮问答会落库（不带则纯代理，不存）
    conversation_id: int | None = None


class ModelsRequest(BaseModel):
    api_key: str
    base_url: str = DEFAULT_BASE_URL


class ConversationCreate(BaseModel):
    title: str = ""


class MessageCreate(BaseModel):
    role: str
    content: str
    model: str | None = None


class ConversationOut(BaseModel):
    # from_attributes：允许直接把 ORM 对象交给响应模型序列化
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    model: str | None = None
    status: str
    created_at: datetime
