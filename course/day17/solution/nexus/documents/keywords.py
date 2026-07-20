"""关键词统计与正则检索。"""

import re


def normalize_keywords(raw_keywords):
    """去空白、去重、保序。"""
    if isinstance(raw_keywords, str):
        items = raw_keywords.split(",")
    else:
        items = list(raw_keywords)
    seen = set()
    normalized = []
    for item in items:
        keyword = item.strip()
        if keyword == "" or keyword in seen:
            continue
        seen.add(keyword)
        normalized.append(keyword)
    return normalized


def count_keyword(text, keyword):
    """对中英文关键词做 re.escape 后计数。"""
    pattern = re.compile(re.escape(keyword), flags=re.IGNORECASE)
    return len(pattern.findall(text))


def count_keywords(text, keywords):
    """统计多个关键词出现次数。"""
    totals = {}
    for keyword in normalize_keywords(keywords):
        totals[keyword] = count_keyword(text, keyword)
    return totals


def merge_keyword_totals(base, extra):
    """合并两份关键词统计。"""
    merged = dict(base)
    for keyword, count in extra.items():
        merged[keyword] = merged.get(keyword, 0) + count
    return merged


def search_snippets(text, keyword, limit=2, window=20):
    """返回关键词附近文本片段，供 CLI 展示。"""
    pattern = re.compile(re.escape(keyword), flags=re.IGNORECASE)
    snippets = []
    for match in pattern.finditer(text):
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        snippet = text[start:end].replace("\n", " ")
        snippets.append(snippet.strip())
        if len(snippets) >= limit:
            break
    return snippets
