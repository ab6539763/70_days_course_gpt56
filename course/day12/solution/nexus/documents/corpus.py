"""语料索引与批量导入。"""

from datetime import datetime, timezone

from nexus.documents.keywords import count_keywords, merge_keyword_totals, normalize_keywords
from nexus.documents.loader import discover_documents, load_document
from nexus.exceptions import DocumentLoadError


def empty_document_index(corpus_dir="corpus"):
    return {
        "corpus_dir": corpus_dir,
        "documents": [],
        "keyword_totals": {},
        "last_ingested_at": None,
    }


class DocumentRecord:
    """单份语料文件的索引记录。"""

    def __init__(self, doc_id, filename, suffix, char_count, keyword_hits):
        self.doc_id = doc_id
        self.filename = filename
        self.suffix = suffix
        self.char_count = char_count
        self.keyword_hits = dict(keyword_hits)

    def to_dict(self):
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "suffix": self.suffix,
            "char_count": self.char_count,
            "keyword_hits": self.keyword_hits,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["doc_id"],
            data["filename"],
            data["suffix"],
            data["char_count"],
            data.get("keyword_hits", {}),
        )


class CorpusService:
    """批量读取语料并维护关键词统计。"""

    def __init__(self, document_index):
        self.document_index = document_index
        self._text_cache = {}

    @property
    def documents(self):
        return [DocumentRecord.from_dict(item) for item in self.document_index["documents"]]

    def ingest_directory(self, corpus_dir, keywords):
        keyword_list = normalize_keywords(keywords)
        if not keyword_list:
            raise DocumentLoadError("至少提供一个关键词")
        paths = discover_documents(corpus_dir)
        if not paths:
            raise DocumentLoadError("目录下没有可导入的语料文件")
        records = []
        totals = {}
        for index, path in enumerate(paths, start=1):
            text = load_document(path)
            hits = count_keywords(text, keyword_list)
            doc_id = f"D{index:03d}"
            record = DocumentRecord(
                doc_id=doc_id,
                filename=path.name,
                suffix=path.suffix.lower(),
                char_count=len(text),
                keyword_hits=hits,
            )
            records.append(record)
            totals = merge_keyword_totals(totals, hits)
            self._text_cache[path.name] = text
        self.document_index["corpus_dir"] = str(corpus_dir)
        self.document_index["documents"] = [item.to_dict() for item in records]
        self.document_index["keyword_totals"] = totals
        self.document_index["last_ingested_at"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        return len(records), totals

    def top_keywords(self, limit=5):
        pairs = sorted(
            self.document_index.get("keyword_totals", {}).items(),
            key=lambda item: (-item[1], item[0]),
        )
        return pairs[:limit]

    def search_keyword(self, keyword):
        keyword = keyword.strip()
        if keyword == "":
            return []
        matched = []
        for record in self.documents:
            hits = record.keyword_hits.get(keyword, 0)
            if hits == 0:
                hits = count_keywords(self._text_cache.get(record.filename, ""), [keyword]).get(
                    keyword, 0
                )
            if hits > 0:
                matched.append((record, hits))
        return sorted(matched, key=lambda item: (-item[1], item[0].doc_id))
