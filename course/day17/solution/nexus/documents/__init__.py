"""文档语料层导出。"""

from nexus.documents.corpus import CorpusService, DocumentRecord, empty_document_index
from nexus.documents.keywords import count_keyword, count_keywords, normalize_keywords
from nexus.documents.loader import discover_documents, load_document

__all__ = [
    "CorpusService",
    "DocumentRecord",
    "empty_document_index",
    "count_keyword",
    "count_keywords",
    "normalize_keywords",
    "discover_documents",
    "load_document",
]
