"""Provider 层：可重试状态码的重试行为。

退避睡眠在测试里被置零——这里验证的是"又发了一次请求"，
不是真等 0.5s/1s（否则每个重试用例都要真等，测试会变慢）。
"""

import asyncio

import httpx

from app.providers import deepseek
from app.providers.deepseek import request_with_retry


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(deepseek, "backoff_seconds", lambda attempt: 0)

    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, json={"error": {"message": "rate limited"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    async def call():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await request_with_retry(
                "test-rid",
                client,
                "POST",
                "https://upstream.test/chat/completions",
                {},
                {"model": "test-model"},
            )

    resp, error = asyncio.run(call())

    assert error is None
    assert resp is not None
    assert resp.status_code == 200
    assert len(attempts) == 2
