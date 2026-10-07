"""Chat 的 service 层与 router 层。

- service：注入 MockTransport 隔离上游，验证"上游响应 → 业务结果"的解析
- router：monkeypatch 掉 service，验证"业务结果 → HTTP 响应"的映射

两层分开测：失败时能立刻看出是解析坏了还是映射坏了。
"""

import asyncio

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ChatMessage, ChatRequest
from app.services.chat import complete_chat, stream_chat


def test_complete_chat_returns_content_and_upstream_model():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "upstream-real-model",
                "choices": [{"message": {"role": "assistant", "content": "你好"}}],
            },
        )

    async def run():
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="hi")],
            api_key="test-key",
        )
        return await complete_chat(
            "test-rid", req, transport=httpx.MockTransport(handler)
        )

    result, error = asyncio.run(run())

    assert error is None
    assert result is not None
    assert result.content == "你好"
    assert result.model == "upstream-real-model"


def test_chat_endpoint_maps_service_error_to_502(monkeypatch):
    async def failing_complete(rid, req, transport=None):
        return None, "连接 LLM 服务失败: boom"

    monkeypatch.setattr("app.routers.chat.complete_chat", failing_complete)

    client = TestClient(app)
    resp = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "api_key": "test-key",
        },
    )

    assert resp.status_code == 502
    assert resp.json() == {"error": "连接 LLM 服务失败: boom"}


def _make_stream_chat_env(monkeypatch, chunks):
    """把落库和上游都换成假的，返回落库记录列表。"""
    persisted = []

    async def fake_persist(rid, conversation_id, role, content, model, status):
        persisted.append((role, content, status))

    async def fake_stream_llm(rid, url, headers, payload):
        for chunk in chunks:
            yield chunk

    monkeypatch.setattr("app.services.chat._persist", fake_persist)
    monkeypatch.setattr("app.services.chat.stream_llm", fake_stream_llm)
    return persisted


def _stream_chat_request():
    return ChatRequest(
        messages=[ChatMessage(role="user", content="hi")],
        api_key="test-key",
        conversation_id=1,
    )


def test_stream_chat_persists_complete_on_normal_finish(monkeypatch):
    persisted = _make_stream_chat_env(
        monkeypatch, ["__MODEL__:test-model\n", "你", "好"]
    )

    async def run():
        async for _ in stream_chat("test-rid", _stream_chat_request()):
            pass

    asyncio.run(run())

    assert ("user", "hi", "complete") in persisted
    assert ("assistant", "你好", "complete") in persisted


def test_stream_chat_keeps_partial_content_as_interrupted(monkeypatch):
    """客户端中途停止：已经生成的部分要留下来，并标记 interrupted。"""
    persisted = _make_stream_chat_env(
        monkeypatch, ["__MODEL__:test-model\n", "你", "好", "这一段不该被读到"]
    )

    async def run():
        gen = stream_chat("test-rid", _stream_chat_request())
        assert await gen.__anext__() == "__MODEL__:test-model\n"
        assert await gen.__anext__() == "你"
        assert await gen.__anext__() == "好"
        await gen.aclose()  # 模拟客户端断开 / 点停止

    asyncio.run(run())

    assert ("user", "hi", "complete") in persisted
    assert ("assistant", "你好", "interrupted") in persisted
