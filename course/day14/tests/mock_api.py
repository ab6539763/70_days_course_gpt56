"""测试用 OpenAI 兼容 Mock API 服务器。"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _MockChatHandler(BaseHTTPRequestHandler):
    reply_text = "HTTP mock 回复：已收到请求"
    fail_remaining = 0

    def log_message(self, format, *args):
        return

    def do_POST(self):
        if _MockChatHandler.fail_remaining > 0:
            _MockChatHandler.fail_remaining -= 1
            encoded = b'{"error":"temporary"}'
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        last_user = ""
        for item in reversed(payload.get("messages", [])):
            if item.get("role") == "user":
                last_user = item.get("content", "")
                break
        content = f"{self.reply_text}｜{last_user[:30]}"
        body = {
            "id": "mock-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        }
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def set_fail_count(count):
    _MockChatHandler.fail_remaining = count


def start_mock_api_server():
    """启动本地 Mock API，返回 (server, base_url)。"""
    _MockChatHandler.fail_remaining = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockChatHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}/v1"
