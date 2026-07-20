"""NexusAI 平台全局常量。"""

DATA_FILE = "nexus_platform.json"
SCHEMA_VERSION = 4
APP_VERSION = "0.0.18"
DEFAULT_STREAM_CHUNK_SIZE = 4
DEFAULT_HISTORY_WINDOW = 20
MAX_HISTORY_WINDOW = 200
CORPUS_DIR = "corpus"
VALID_DEPARTMENTS = ("客户服务部", "销售部", "财务部", "技术部", "产品部")
DEFAULT_MODEL_CONFIG = {
    "provider": "qwen",
    "model_id": "qwen-plus",
    "temperature": 0.7,
    "max_tokens": 1024,
}
