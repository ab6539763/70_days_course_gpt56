"""HTTP 流式客户端：OpenAI 兼容 SSE 解析。"""

from __future__ import annotations

import json
from typing import Dict, Generator, Iterable

import requests

from nexus.exceptions import ApiCallError
from nexus.http.client import Headers, JsonPayload
from nexus.observability.logging import get_logger, log_event


_stream_logger = get_logger("http")
DEFAULT_STREAM_TIMEOUT = 120


def extract_stream_delta(chunk: dict) -> str:
    """从 Chat Completions 流式 chunk 提取 content delta。"""
    choices = chunk.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    return content if isinstance(content, str) else ""


def iter_sse_data_lines(response: requests.Response) -> Generator[str, None, None]:
    """逐行读取 SSE data 字段。"""
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        yield payload


def post_stream_json(
    url: str,
    headers: Headers,
    payload: JsonPayload,
    timeout: int = DEFAULT_STREAM_TIMEOUT,
) -> Generator[dict, None, None]:
    """POST 流式请求，逐条 yield 解析后的 SSE JSON chunk。"""
    log_event(_stream_logger, 20, "http_stream_start", url=url, timeout=timeout)
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout,
        )
    except requests.Timeout as error:
        log_event(_stream_logger, 40, "http_stream_timeout", url=url, timeout=timeout)
        raise ApiCallError(f"流式请求超时（>{timeout}s）：{url}") from error
    except requests.RequestException as error:
        log_event(_stream_logger, 40, "http_stream_network", url=url, error=str(error))
        raise ApiCallError(f"流式网络请求失败：{error}") from error
    if response.status_code >= 400:
        snippet = response.text[:300].replace("\n", " ")
        log_event(
            _stream_logger,
            40,
            "http_stream_error",
            url=url,
            status=response.status_code,
        )
        raise ApiCallError(
            f"HTTP {response.status_code}：{snippet or '无响应体'}"
        )
    try:
        for line in iter_sse_data_lines(response):
            try:
                parsed = json.loads(line)
            except ValueError as error:
                log_event(_stream_logger, 40, "http_stream_json", url=url, error=str(error))
                raise ApiCallError(f"SSE 行不是合法 JSON：{line[:120]}") from error
            yield parsed
        log_event(_stream_logger, 20, "http_stream_ok", url=url)
    finally:
        response.close()


def collect_stream_text(chunks: Iterable[dict]) -> str:
    """把流式 chunk 序列拼成完整 assistant 文本。"""
    parts = []
    for chunk in chunks:
        delta = extract_stream_delta(chunk)
        if delta:
            parts.append(delta)
    return "".join(parts)
