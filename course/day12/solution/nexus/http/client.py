"""HTTP 客户端：requests 封装与错误语义。"""

import requests

from nexus.exceptions import ApiCallError


DEFAULT_TIMEOUT = 30


def post_json(url, headers, payload, timeout=DEFAULT_TIMEOUT):
    """发送 POST JSON 请求并返回解析后的 dict。"""
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.Timeout as error:
        raise ApiCallError(f"请求超时（>{timeout}s）：{url}") from error
    except requests.RequestException as error:
        raise ApiCallError(f"网络请求失败：{error}") from error
    if response.status_code >= 400:
        snippet = response.text[:300].replace("\n", " ")
        raise ApiCallError(
            f"HTTP {response.status_code}：{snippet or '无响应体'}"
        )
    try:
        return response.json()
    except ValueError as error:
        raise ApiCallError(f"响应不是合法 JSON：{error}") from error


def build_bearer_headers(api_key):
    """OpenAI / 兼容模式通用 Authorization 头。"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
