"""Offline evidence extraction. No hidden language model or canned QA mapping."""

from dataclasses import dataclass

from .retrieval import Hit, Retriever


@dataclass
class Answer:
    query: str
    mode: str
    abstained: bool
    confidence: float
    threshold: float
    passages: list[dict]
    hits: list[dict]

    def to_dict(self) -> dict:
        return vars(self)


def answer(retriever: Retriever, query: str, method: str = "rrf", threshold: float = .16, top_k: int = 3) -> Answer:
    """Use the top hit's char cosine as a heuristic, not a calibrated probability.

    Return exact source chunks. Retrieving a passage does not establish entailment.
    The threshold is a dev-selected operating point; see evaluate.py.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1]")
    hits = retriever.search(query, method=method, top_k=top_k)
    confidence = hits[0].cosine if hits else 0.0
    abstained = not hits or confidence < threshold
    passages = [] if abstained else [{"chunk_id": hit.chunk.id, "citation": hit.chunk.citation, "text": hit.chunk.text} for hit in hits[:2]]
    return Answer(query, "offline-extractive", abstained, confidence, threshold, passages, [hit.to_dict() for hit in hits])
