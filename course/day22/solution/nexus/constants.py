"""NexusAI 平台全局常量。"""

DATA_FILE = "nexus_platform.json"
SCHEMA_VERSION = 4
APP_VERSION = "0.0.22"
REVISION_HEADER = "X-Expected-Revision"
DEFAULT_AUDIT_DIR = "audit"
DEFAULT_AUDIT_MAX_ENTRIES = 500
DEFAULT_STREAM_CHUNK_SIZE = 4
DEFAULT_STREAM_RESUME_TTL = 300
RESUME_TOKEN_PREFIX = "rst_"
DEFAULT_HISTORY_WINDOW = 20
MAX_HISTORY_WINDOW = 200
DEFAULT_SESSION_DIR = "sessions"
SESSION_ID_PREFIX = "nxs_"
SESSION_ID_PATTERN = r"nxs_[0-9a-f]{32}"
SESSION_HEADER = "X-Session-Id"
CORPUS_DIR = "corpus"
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部", "技术部", "产品部")
DEFAULT_MODEL_CONFIG = {
    "provider": "qwen",
    "model_id": "qwen-plus",
    "temperature": 0.7,
    "max_tokens": 1024,
}
