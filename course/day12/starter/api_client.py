"""Day 12 课堂起步：第一次 requests POST。"""

# TODO: import requests
# TODO: 设置 headers 与 json body
# TODO: 捕获 requests.Timeout / RequestException


def demo_post(url, api_key, messages):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": "demo", "messages": messages}
    # response = requests.post(url, headers=headers, json=payload, timeout=30)
    # return response.json()
    return payload


if __name__ == "__main__":
    print(demo_post("https://example.test/v1/chat/completions", "sk-demo", []))
