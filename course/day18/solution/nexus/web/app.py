"""Flask 应用工厂。"""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from nexus.constants import APP_VERSION, DATA_FILE
from nexus.web.routes import register_routes
from nexus.web.state_manager import WebStateManager


WEB_ROOT = Path(__file__).resolve().parent


def create_app(data_file=DATA_FILE):
    """创建 Web 对话工作台 Flask 应用。"""
    app = Flask(
        __name__,
        template_folder=str(WEB_ROOT / "templates"),
        static_folder=str(WEB_ROOT / "static"),
    )
    app.config["APP_VERSION"] = APP_VERSION
    app.config["DATA_FILE"] = data_file
    app.config["STATE_MANAGER"] = WebStateManager(data_file)
    register_routes(app)
    return app
