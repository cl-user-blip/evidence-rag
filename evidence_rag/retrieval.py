"""BM25, character TF-IDF, and Reciprocal Rank Fusion, without neural weights."""

from collections import Counter
from dataclasses import dataclass
import math
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .ingest import Chunk

EN_STOP = set("a an the is are was were be been to for on in of and or with how what which why do does should can i we it from when about".split())
ZH_STOP = {"如何", "什么", "为什么", "怎么", "是否", "一个", "我们", "进行", "这个", "哪些", "时候"}
METHODS = ("bm25", "tfidf", "rrf")


def tokenize(text: str) -> list[str]:
    """English terms + CJK bigrams; no trained segmenter or synonym oracle."""
    text = text.lower()
    terms = [word for word in re.findall(r"[a-z0-9][a-z0-9_+.-]*", text) if word not in EN_STOP]
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        terms.extend(run[i:i + 2] for i in range(len(run) - 1) if run[i:i + 2] not in ZH_STOP)
        if len(run) == 1:
            terms.append(run)
    return terms


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    if k < 0:
        raise ValueError("RRF k must be nonnegative")
    scores: dict[int, float] = {}
    for ranking in rankings:
        seen: set[int] = set()
        for rank, index in enumerate(ranking, 1):
            if index in seen:
                continue
            scores[index] = scores.get(index, 0.0) + 1.0 / (k + rank)
            seen.add(index)
    return scores


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float
    bm25: float
    cosine: float

    def to_dict(self) -> dict:
        return {**self.chunk.to_dict(), "citation": self.chunk.citation,
                "score": self.score, "bm25": self.bm25, "cosine": self.cosine}


class Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        if not chunks:
            raise ValueError("No nonempty Markdown chunks found")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 requires k1 > 0 and b in [0, 1]")
        self.chunks, self.k1, self.b = chunks, k1, b
        self.counts = [Counter(tokenize(chunk.text)) for chunk in chunks]
        self.lengths = np.array([sum(count.values()) for count in self.counts], dtype=float)
        self.avgdl = max(float(self.lengths.mean()), 1.0)
        df = Counter(term for count in self.counts for term in count)
        self.idf = {term: math.log(1 + (len(chunks) - n + .5) / (n + .5)) for term, n in df.items()}
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), sublinear_tf=True, norm="l2")
        try:
            self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])
        except ValueError as exc:
            raise ValueError("Corpus needs at least one two-character text span") from exc

    def component_scores(self, query: str) -> tuple[np.ndarray, np.ndarray]:
        bm25 = np.zeros(len(self.chunks))
        for term in set(tokenize(query)):
            tf = np.array([count[term] for count in self.counts], dtype=float)
            denom = tf + self.k1 * (1 - self.b + self.b * self.lengths / self.avgdl)
            bm25 += self.idf.get(term, 0.0) * tf * (self.k1 + 1) / np.maximum(denom, 1e-12)
        cosine = (self.matrix @ self.vectorizer.transform([query]).T).toarray().ravel()
        return bm25, cosine

    def search(self, query: str, method: str = "rrf", top_k: int = 5) -> list[Hit]:
        if method not in METHODS or top_k <= 0:
            raise ValueError(f"method must be one of {METHODS}; top_k must be positive")
        if not query.strip():
            return []
        bm25, cosine = self.component_scores(query)

        def ranked(scores):
            return sorted((i for i, s in enumerate(scores) if s > 1e-12), key=lambda i: (-scores[i], self.chunks[i].id))

        if method == "rrf":
            fused = reciprocal_rank_fusion([ranked(bm25)[:50], ranked(cosine)[:50]])
            order = sorted(fused, key=lambda i: (-fused[i], self.chunks[i].id))[:top_k]
            return [Hit(self.chunks[i], float(fused[i]), float(bm25[i]), float(cosine[i])) for i in order]
        scores = bm25 if method == "bm25" else cosine
        return [Hit(self.chunks[i], float(scores[i]), float(bm25[i]), float(cosine[i])) for i in ranked(scores)[:top_k]]
