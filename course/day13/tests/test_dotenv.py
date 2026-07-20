"""Day 13 dotenv 与配置加载单测。"""

import os
import sys
import tempfile
from pathlib import Path


SOLUTION = Path(__file__).parents[1] / "solution"
sys.path.insert(0, str(SOLUTION))

from nexus.config.env_loader import load_env, mask_secret, reset_env_loader_state
from nexus.http.config import bootstrap_env, reset_bootstrap, resolve_api_key


with tempfile.TemporaryDirectory(prefix="nexus-day13-dotenv-") as temporary:
    env_file = Path(temporary) / ".env"
    env_file.write_text(
        "NEXUS_API_KEY=dotenv-secret-key\nNEXUS_USE_MOCK=0\n",
        encoding="utf-8",
    )
    os.environ.pop("NEXUS_API_KEY", None)
    reset_bootstrap()
    reset_env_loader_state()
    loaded = load_env(str(env_file), override=True)
    assert loaded.endswith(".env")
    reset_bootstrap()
    assert resolve_api_key() == "dotenv-secret-key"

assert mask_secret("sk-abcdef1234") == "*********1234"
assert mask_secret("") == "(未设置)"

print("Day 13 dotenv 单测通过：.env 加载与密钥脱敏均正确。")
