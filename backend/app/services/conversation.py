"""会话与消息的业务逻辑（读写 MySQL）。

这一层只依赖 AsyncSession，不碰 HTTP —— 路由层负责把结果映射成响应。
"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message, User

DEFAULT_USERNAME = "default"


async def get_or_create_default_user(session: AsyncSession) -> User:
    """当前项目还没有登录，先用一个固定的默认用户占位。

    存在即返回，不存在则创建——重复调用安全。
    """
    user = await session.scalar(select(User).where(User.username == DEFAULT_USERNAME))
    if user is None:
        user = User(username=DEFAULT_USERNAME)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def list_conversations(session: AsyncSession, user_id: int) -> list[Conversation]:
    result = await session.scalars(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    )
    return list(result)


async def create_conversation(
    session: AsyncSession, user_id: int, title: str = ""
) -> Conversation:
    conversation = Conversation(user_id=user_id, title=title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def get_conversation(session: AsyncSession, conversation_id: int) -> Conversation | None:
    return await session.get(Conversation, conversation_id)


async def delete_conversation(session: AsyncSession, conversation_id: int) -> bool:
    """删除会话；消息由外键 ON DELETE CASCADE 一并清理。"""
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        return False
    await session.delete(conversation)
    await session.commit()
    return True


async def list_messages(session: AsyncSession, conversation_id: int) -> list[Message]:
    result = await session.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id)
    )
    return list(result)


async def add_message(
    session: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
    model: str | None = None,
    status: str = "complete",
) -> Message:
    """追加一条消息，并把所属会话的 updated_at 顶到最新。

    插入消息不会 UPDATE conversations 那一行，所以 onupdate 不会触发——
    侧边栏按 updated_at 排序，必须显式刷新它，否则聊过的会话永远沉在下面。
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model,
        status=status,
    )
    session.add(message)
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=func.now())
    )
    await session.commit()
    await session.refresh(message)
    return message
