"""Day 11 课堂起步：pathlib 发现语料与 UTF-8 读取。"""

from pathlib import Path

# TODO: 用 with open(..., encoding="utf-8") 读取文本
# TODO: 用 path.suffix 过滤 .txt/.md
# TODO: 捕获 UnicodeDecodeError 并给出友好提示


def list_text_files(corpus_dir):
    root = Path(corpus_dir)
    return [path for path in root.rglob("*.txt") if path.is_file()]


if __name__ == "__main__":
    for path in list_text_files("corpus"):
        print(path.name)
