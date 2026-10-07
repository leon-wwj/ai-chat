"""会话与消息接口。

路由层只做三件事：接参数、调 service、映射状态码。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.schemas import ConversationCreate, ConversationOut, MessageCreate, MessageOut
from app.services import conversation as conv

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def list_conversations(session: AsyncSession = Depends(get_session)):
    user = await conv.get_or_create_default_user(session)
    return await conv.list_conversations(session, user.id)


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    user = await conv.get_or_create_default_user(session)
    return await conv.create_conversation(session, user.id, payload.title)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
):
    deleted = await conv.delete_conversation(session, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
):
    if await conv.get_conversation(session, conversation_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return await conv.list_messages(session, conversation_id)


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def add_message(
    conversation_id: int,
    payload: MessageCreate,
    session: AsyncSession = Depends(get_session),
):
    if await conv.get_conversation(session, conversation_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return await conv.add_message(
        session, conversation_id, payload.role, payload.content, payload.model
    )
