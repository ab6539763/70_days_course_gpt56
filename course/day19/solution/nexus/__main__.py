"""允许 python -m nexus 启动 CLI。"""

from nexus.cli.app import run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli())
