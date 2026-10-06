"""Provider 层：流式 SSE 解析与超时预算。

上游用 httpx.MockTransport 注入——stream_llm 的 transport 参数就是给测试留的口子。
"""

import asyncio
from collections.abc import Callable

import httpx

from app.providers import deepseek
from app.providers.deepseek import stream_llm

Handler = Callable[[httpx.Request], httpx.Response]


def _sse_response(*events: str) -> httpx.Response:
    body = "".join(f"data: {event}\n\n" for event in events)
    return httpx.Response(200, content=body.encode("utf-8"))


def _collect(handler: Handler) -> list[str]:
    async def run() -> list[str]:
        chunks: list[str] = []
        async for chunk in stream_llm(
            "test-rid",
            "https://upstream.test/chat/completions",
            {},
            {},
            transport=httpx.MockTransport(handler),
        ):
            chunks.append(chunk)
        return chunks

    return asyncio.run(run())


def test_parses_sse_into_model_marker_and_content():
    def handler(request: httpx.Request) -> httpx.Response:
        return _sse_response(
            '{"model":"test-model","choices":[{"delta":{"content":"你"}}]}',
            '{"choices":[{"delta":{"content":"好"}}]}',
            "[DONE]",
        )

    chunks = _collect(handler)

    assert chunks[0] == "__MODEL__:test-model\n"
    assert "".join(chunks[1:]) == "你好"


def test_yields_error_when_total_budget_exceeded(monkeypatch):
    # 预算设为负数：第一行数据就必然超时，不用真的等 5 分钟。
    monkeypatch.setattr(deepseek, "STREAM_TOTAL_BUDGET_SECONDS", -1)

    def handler(request: httpx.Request) -> httpx.Response:
        return _sse_response(
            '{"choices":[{"delta":{"content":"x"}}]}',
            "[DONE]",
        )

    chunks = _collect(handler)

    assert chunks == ["__ERROR__:生成超时（超过流式总时长预算）"]
