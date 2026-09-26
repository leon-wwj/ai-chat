"""Provider 层：调用上游 LLM 接口的非流式路径。

上游用 httpx.MockTransport 顶替，测试不打真实网络。
"""

import asyncio

import httpx

from app.providers.deepseek import request_with_retry


def test_returns_upstream_response_on_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "你好"}}]},
        )

    async def call():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await request_with_retry(
                "test-rid",
                client,
                "POST",
                "https://upstream.test/chat/completions",
                {"Authorization": "Bearer test-key"},
                {"model": "test-model", "messages": [{"role": "user", "content": "hi"}]},
            )

    resp, error = asyncio.run(call())

    assert error is None
    assert resp is not None
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "你好"
