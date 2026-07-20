"""OpenAPI 3.0 契约：与实现单源对齐。"""

from __future__ import annotations

from nexus.constants import APP_VERSION, MAX_HISTORY_WINDOW


def build_openapi_spec(base_url="http://127.0.0.1:8080"):
    """生成 OpenAPI 3.0 文档 dict。"""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "智枢 NexusAI Web API",
            "version": APP_VERSION,
            "description": "Phase2 Web 对话工作台 REST 契约（Day20 断流恢复）",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/api/session": {
                "get": {
                    "summary": "获取当前会话信息",
                    "operationId": "getSession",
                    "parameters": [{"$ref": "#/components/parameters/SessionHeader"}],
                    "responses": {
                        "200": {
                            "description": "会话元数据",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SessionResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                    },
                },
                "post": {
                    "summary": "创建新会话",
                    "operationId": "createSession",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/SessionCreateRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "新会话已创建",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SessionCreateResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                    },
                },
            },
            "/api/sessions": {
                "get": {
                    "summary": "列举全部会话",
                    "operationId": "listSessions",
                    "responses": {
                        "200": {
                            "description": "会话列表",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SessionListResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/api/health": {
                "get": {
                    "summary": "健康检查",
                    "operationId": "getHealth",
                    "responses": {
                        "200": {
                            "description": "服务正常",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            },
                        },
                        "503": {"$ref": "#/components/responses/ServiceUnavailable"},
                    },
                }
            },
            "/api/messages": {
                "get": {
                    "summary": "获取会话消息",
                    "operationId": "listMessages",
                    "parameters": [{"$ref": "#/components/parameters/SessionHeader"}],
                    "responses": {
                        "200": {
                            "description": "消息列表",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MessagesResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "500": {"$ref": "#/components/responses/InternalError"},
                    },
                }
            },
            "/api/chat": {
                "post": {
                    "summary": "发送对话",
                    "operationId": "postChat",
                    "parameters": [{"$ref": "#/components/parameters/SessionHeader"}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "assistant 回复",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ChatResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "502": {"$ref": "#/components/responses/BadGateway"},
                        "500": {"$ref": "#/components/responses/InternalError"},
                    },
                }
            },
            "/api/chat/stream": {
                "post": {
                    "summary": "流式发送对话（SSE，支持 resume_token 断流恢复）",
                    "operationId": "postChatStream",
                    "parameters": [
                        {"$ref": "#/components/parameters/SessionHeader"},
                        {
                            "name": "X-Stream-Simulate-Interrupt",
                            "in": "header",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 0},
                            "description": "测试钩子：Mock 模式下在第 N 个 chunk 后模拟断流",
                        },
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StreamChatRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "text/event-stream：chunk/resume/interrupted/done/error 事件",
                            "content": {
                                "text/event-stream": {
                                    "schema": {
                                        "type": "string",
                                        "description": "SSE 事件流：chunk、resume、interrupted、done、error",
                                    }
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "410": {"$ref": "#/components/responses/ResumeExpired"},
                        "502": {"$ref": "#/components/responses/BadGateway"},
                        "500": {"$ref": "#/components/responses/InternalError"},
                    },
                }
            },
            "/api/stream/resume/{resume_token}": {
                "get": {
                    "summary": "查询断流恢复上下文",
                    "operationId": "getStreamResume",
                    "parameters": [
                        {"$ref": "#/components/parameters/SessionHeader"},
                        {
                            "name": "resume_token",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "pattern": "rst_[0-9a-f]+"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "恢复上下文元数据",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ResumeInfoResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "410": {"$ref": "#/components/responses/ResumeExpired"},
                    },
                }
            },
            "/api/clear": {
                "post": {
                    "summary": "清空会话",
                    "operationId": "postClear",
                    "parameters": [{"$ref": "#/components/parameters/SessionHeader"}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ClearRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "已清空",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ClearResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "500": {"$ref": "#/components/responses/InternalError"},
                    },
                }
            },
            "/api/window": {
                "get": {
                    "summary": "Token 窗口与 history 统计",
                    "operationId": "getWindow",
                    "parameters": [
                        {"$ref": "#/components/parameters/SessionHeader"},
                        {
                            "name": "max_history",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 0, "maximum": 200},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "窗口快照",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/WindowResponse"}
                                }
                            },
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                    },
                }
            },
            "/api/openapi.json": {
                "get": {
                    "summary": "OpenAPI 规范 JSON",
                    "operationId": "getOpenApi",
                    "responses": {
                        "200": {"description": "OpenAPI 3.0 JSON"},
                    },
                }
            },
        },
        "components": {
            "parameters": {
                "SessionHeader": {
                    "name": "X-Session-Id",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string", "pattern": "nxs_[0-9a-f]{32}"},
                    "description": "会话隔离标识，每会话对应独立 JSON state 文件",
                }
            },
            "schemas": {
                "ApiError": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "required": ["ok", "error", "trace_id"],
                    "properties": {
                        "ok": {"type": "boolean", "enum": [False]},
                        "error": {"$ref": "#/components/schemas/ApiError"},
                        "trace_id": {"type": "string"},
                    },
                },
                "ChatRequest": {
                    "type": "object",
                    "required": ["prompt"],
                    "properties": {
                        "prompt": {"type": "string", "minLength": 1},
                        "system_prompt": {"type": "string"},
                        "max_history": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": MAX_HISTORY_WINDOW,
                            "description": "API 请求携带的非 system 消息条数上限",
                        },
                    },
                },
                "StreamChatRequest": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "system_prompt": {"type": "string"},
                        "max_history": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": MAX_HISTORY_WINDOW,
                        },
                        "resume_token": {
                            "type": "string",
                            "pattern": "rst_[0-9a-f]+",
                            "description": "断流恢复令牌；提供时可省略 prompt",
                        },
                    },
                },
                "ClearRequest": {
                    "type": "object",
                    "properties": {
                        "keep_system": {"type": "boolean", "default": True},
                    },
                },
                "MessageItem": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                        "preview": {"type": "string"},
                    },
                },
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "app_version": {"type": "string"},
                        "trace_id": {"type": "string"},
                        "session_count": {"type": "integer"},
                        "session_dir": {"type": "string"},
                        "pending_resume_count": {"type": "integer"},
                    },
                },
                "SessionCreateRequest": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                    },
                },
                "SessionCreateResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "session_id": {"type": "string"},
                        "owner": {"type": "string"},
                        "revision": {"type": "integer"},
                        "messages": {"type": "integer"},
                    },
                },
                "SessionResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "session_id": {"type": "string"},
                        "owner": {"type": "string"},
                        "revision": {"type": "integer"},
                        "messages": {"type": "integer"},
                        "model": {"type": "string"},
                    },
                },
                "SessionListResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "count": {"type": "integer"},
                        "session_dir": {"type": "string"},
                        "sessions": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/SessionResponse"},
                        },
                    },
                },
                "MessagesResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "messages": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/MessageItem"},
                        },
                    },
                },
                "ChatResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "assistant": {"type": "string"},
                        "revision": {"type": "integer"},
                        "messages": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/MessageItem"},
                        },
                        "window": {"$ref": "#/components/schemas/WindowMeta"},
                    },
                },
                "StreamChunkEvent": {
                    "type": "object",
                    "properties": {
                        "delta": {"type": "string", "description": "assistant 增量文本"},
                    },
                },
                "StreamDoneEvent": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "assistant": {"type": "string"},
                        "revision": {"type": "integer"},
                        "trace_id": {"type": "string"},
                        "resume_token": {"type": "string"},
                        "resumed": {"type": "boolean"},
                        "window": {"$ref": "#/components/schemas/WindowMeta"},
                        "messages": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/MessageItem"},
                        },
                    },
                },
                "StreamInterruptedEvent": {
                    "type": "object",
                    "properties": {
                        "resume_token": {"type": "string"},
                        "partial": {"type": "string"},
                        "expires_at": {"type": "number"},
                        "error": {"type": "string"},
                        "revision": {"type": "integer"},
                    },
                },
                "StreamResumeEvent": {
                    "type": "object",
                    "properties": {
                        "partial": {"type": "string"},
                        "resumed": {"type": "boolean"},
                    },
                },
                "ResumeInfoResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "resume_token": {"type": "string"},
                        "session_id": {"type": "string"},
                        "partial": {"type": "string"},
                        "user_prompt": {"type": "string"},
                        "expires_at": {"type": "number"},
                        "ttl_remaining": {"type": "integer"},
                    },
                },
                "WindowMeta": {
                    "type": "object",
                    "properties": {
                        "history_total": {"type": "integer"},
                        "history_sent": {"type": "integer"},
                        "history_window": {"type": "integer"},
                        "window_applied": {"type": "boolean"},
                        "tokens_estimated_full": {"type": "integer"},
                        "tokens_estimated_sent": {"type": "integer"},
                    },
                },
                "WindowResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "default_history_window": {"type": "integer"},
                        "messages_stored": {"type": "integer"},
                        "history_window": {"type": "integer"},
                        "window_applied": {"type": "boolean"},
                        "tokens_estimated_full": {"type": "integer"},
                        "tokens_estimated_sent": {"type": "integer"},
                    },
                },
                "ClearResponse": {
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "message": {"type": "string"},
                        "revision": {"type": "integer"},
                    },
                },
            },
            "responses": {
                "BadRequest": {
                    "description": "客户端错误",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                },
                "BadGateway": {
                    "description": "上游模型错误",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                },
                "InternalError": {
                    "description": "平台内部错误",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                },
                "ServiceUnavailable": {
                    "description": "服务不可用",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                },
                "ResumeExpired": {
                    "description": "resume_token 不存在或已过期",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                },
            },
        },
    }
