"""测试用 OpenAI 兼容 Mock API 服务器（含流式 SSE）。"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _MockChatHandler(BaseHTTPRequestHandler):
    reply_text = "HTTP mock 回复：已收到请求"
    fail_remaining = 0

    def log_message(self, format, *args):
        return

    def _last_user(self, payload):
        for item in reversed(payload.get("messages", [])):
            if item.get("role") == "user":
                return item.get("content", "")
        return ""

    def _write_json(self, status, body):
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _write_sse_chunks(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.end_headers()
        step = 8
        for index in range(0, len(content), step):
            piece = content[index : index + step]
            chunk = {
                "choices": [{"index": 0, "delta": {"content": piece}}],
            }
            line = f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8")
            self.wfile.write(line)
        self.wfile.write(b"data: [DONE]\n\n")

    def do_POST(self):
        if _MockChatHandler.fail_remaining > 0:
            _MockChatHandler.fail_remaining -= 1
            self._write_json(503, {"error": "temporary"})
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        last_user = self._last_user(payload)
        content = f"{self.reply_text}｜{last_user[:30]}"
        if payload.get("stream"):
            self._write_sse_chunks(content)
            return
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
        self._write_json(200, body)


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
