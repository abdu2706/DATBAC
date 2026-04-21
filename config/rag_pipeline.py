from __future__ import annotations

import re
from typing import Dict, List, Tuple

from rank_bm25 import BM25Okapi

from .rag import TOP_K


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").lower())


class RAGPipeline:
    def __init__(self):
        self._case_docs: dict[str, list[dict]] = {}
        self._case_bm25: dict[str, BM25Okapi] = {}

    def index_case(self, case_id: str, sentences: Dict[str, Dict]):
        """Index case sentences for BM25 retrieval."""
        if case_id in self._case_docs:
            return

        docs: list[dict] = []
        for sid, sent in sentences.items():
            text = sent.get("text", "")
            docs.append(
                {
                    "sid": str(sid),
                    "text": text,
                    "tokens": _tokenize(text),
                    "paragraph_id": sent.get("paragraph_id", ""),
                }
            )
        self._case_docs[case_id] = docs
        self._case_bm25[case_id] = BM25Okapi([d["tokens"] for d in docs])

    def retrieve(self, query: str, case_id: str, top_k: int = TOP_K) -> List[Tuple[str, str, float]]:
        docs = self._case_docs.get(case_id, [])
        if not docs:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            scores = [0.0 for _ in docs]
        else:
            bm25 = self._case_bm25[case_id]
            scores = bm25.get_scores(query_tokens).tolist()

        ranked = sorted(zip(docs, scores), key=lambda item: item[1], reverse=True)
        top = ranked[: max(0, top_k)]
        return [(d["sid"], d["text"], score) for d, score in top]

    def retrieve_all_ranked(self, query: str, case_id: str) -> List[Tuple[str, str, float]]:
        docs = self._case_docs.get(case_id, [])
        if not docs:
            return []
        return self.retrieve(query, case_id, top_k=len(docs))
