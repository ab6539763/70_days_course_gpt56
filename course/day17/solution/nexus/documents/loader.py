"""文档加载与编码处理。"""

import csv
import json
from pathlib import Path

from nexus.exceptions import DocumentLoadError


ALLOWED_SUFFIXES = {".txt", ".md", ".csv", ".json"}


def read_text_file(path):
    """使用 UTF-8 与上下文管理器读取文本文件。"""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        raise DocumentLoadError(f"无法读取文件 {path.name}：{error}") from error
    except UnicodeDecodeError as error:
        raise DocumentLoadError(
            f"文件 {path.name} 不是 UTF-8 编码，请转换后再导入"
        ) from error


def load_csv_as_text(path):
    """把 CSV 所有单元格拼接为可检索文本。"""
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            cells = [cell.strip() for row in reader for cell in row if cell.strip()]
        return " ".join(cells)
    except OSError as error:
        raise DocumentLoadError(f"无法读取 CSV {path.name}：{error}") from error
    except csv.Error as error:
        raise DocumentLoadError(f"CSV 格式错误 {path.name}：{error}") from error


def load_json_as_text(path):
    """优先提取 content 字段，否则序列化为紧凑 JSON 字符串。"""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as error:
        raise DocumentLoadError(f"无法读取 JSON {path.name}：{error}") from error
    except json.JSONDecodeError as error:
        raise DocumentLoadError(f"JSON 解析失败 {path.name}：{error}") from error
    if isinstance(payload, dict) and isinstance(payload.get("content"), str):
        return payload["content"]
    return json.dumps(payload, ensure_ascii=False)


def load_document(path):
    """根据后缀选择读取策略，返回归一化文本。"""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise DocumentLoadError(f"不支持的文件类型：{suffix}")
    if suffix == ".csv":
        return load_csv_as_text(file_path)
    if suffix == ".json":
        return load_json_as_text(file_path)
    return read_text_file(file_path)


def discover_documents(corpus_dir):
    """用 pathlib 递归发现语料文件，跳过隐藏文件。"""
    root = Path(corpus_dir)
    if not root.exists():
        raise DocumentLoadError(f"语料目录不存在：{root}")
    if not root.is_dir():
        raise DocumentLoadError(f"语料路径不是目录：{root}")
    paths = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() in ALLOWED_SUFFIXES:
            paths.append(path)
    return paths
