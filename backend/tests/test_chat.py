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
from app.services.chat import complete_chat


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
