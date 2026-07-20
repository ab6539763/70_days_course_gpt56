"""OpenAPI 3.0 契约：与实现单源对齐。"""

from __future__ import annotations

from nexus.constants import APP_VERSION


def build_openapi_spec(base_url="http://127.0.0.1:8080"):
    """生成 OpenAPI 3.0 文档 dict。"""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "智枢 NexusAI Web API",
            "version": APP_VERSION,
            "description": "Phase2 Web 对话工作台 REST 契约（Day16 标准错误码）",
        },
        "servers": [{"url": base_url}],
        "paths": {
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
            "/api/clear": {
                "post": {
                    "summary": "清空会话",
                    "operationId": "postClear",
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
                        "revision": {"type": "integer"},
                        "model": {"type": "string"},
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
            },
        },
    }
