"""NexusAI 0.0.13 主入口：启动前加载 .env。"""

from nexus.http.config import bootstrap_env
from nexus.cli.app import run_cli


if __name__ == "__main__":
    bootstrap_env()
    raise SystemExit(run_cli())
