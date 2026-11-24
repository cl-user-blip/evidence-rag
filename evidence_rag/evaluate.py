"""Document-level retrieval and separately reported abstention evaluation."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
from statistics import mean
import time

import numpy as np
import sklearn

from .answer import answer
from .ingest import ingest
from .retrieval import METHODS, Retriever


def document_ranking(hits) -> list[str]:
    return list(dict.fromkeys(hit.chunk.source for hit in hits))


def retrieval_metrics(ranked: list[str], relevant: list[str], k: int) -> dict[str, float]:
    if not relevant or k <= 0:
        raise ValueError("Retrieval metrics require relevant documents and k > 0")
    ranked = list(dict.fromkeys(ranked))[:k]
    relevant_set = set(relevant)
    found = [int(source in relevant_set) for source in ranked]
    recall = sum(found) / len(relevant_set)
    rr = next((1 / (i + 1) for i, value in enumerate(found) if value), 0.0)
    dcg = sum(value / math.log2(i + 2) for i, value in enumerate(found))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant_set))))
    return {f"recall@{k}": recall, f"mrr@{k}": rr, f"ndcg@{k}": dcg / ideal}


def classification_metrics(labels: list[bool], predictions: list[bool]) -> dict[str, float | int]:
    """Positive means answerable/accepted, not retrieval correctness."""
    tp = sum(y and p for y, p in zip(labels, predictions))
    fp = sum(not y and p for y, p in zip(labels, predictions))
    tn = sum(not y and not p for y, p in zip(labels, predictions))
    fn = sum(y and not p for y, p in zip(labels, predictions))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    specificity = tn / max(tn + fp, 1)
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / max(precision + recall, 1e-12),
            "balanced_accuracy": (recall + specificity) / 2,
            "false_accept_rate": fp / max(fp + tn, 1)}


def select_threshold(retriever: Retriever, dev: list[dict], method: str) -> tuple[float, dict]:
    if not dev or {bool(q["relevant"]) for q in dev} != {False, True}:
        raise ValueError("dev must contain answerable and unanswerable queries")
    results = [answer(retriever, q["query"], method=method, threshold=0) for q in dev]
    labels = [bool(q["relevant"]) for q in dev]
    candidates = sorted({0.0, 1.0, *(round(a.confidence + 1e-9, 10) for a in results)})
    rows = []
    for threshold in candidates:
        predictions = [bool(a.hits) and a.confidence >= threshold for a in results]
        metrics = classification_metrics(labels, predictions)
        rows.append((metrics["balanced_accuracy"], metrics["f1"], threshold, metrics))
    _, _, threshold, metrics = max(rows, key=lambda row: (row[0], row[1], row[2]))
    return threshold, metrics


def evaluate(corpus: Path, queries_path: Path, top_k: int = 3, max_chars: int = 320) -> dict:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    queries = json.loads(queries_path.read_text(encoding="utf-8"))
    ids = [q["id"] for q in queries]
    if len(ids) != len(set(ids)) or any(q["split"] not in ("dev", "test") for q in queries):
        raise ValueError("Query IDs must be unique and split must be dev or test")
    chunks = ingest(corpus, max_chars=max_chars)
    sources = {c.source for c in chunks}
    if any(not set(q["relevant"]).issubset(sources) for q in queries):
        raise ValueError("A relevance label references a missing source")
    retriever = Retriever(chunks)
    dev, test = ([q for q in queries if q["split"] == split] for split in ("dev", "test"))
    if not test or not any(q["relevant"] for q in test):
        raise ValueError("Test split must contain answerable queries")
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Original curated bilingual fixture; not a production or public-benchmark result.",
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__},
        "corpus_sha256": sha256("\n".join(f"{c.id}:{c.text}" for c in chunks).encode()).hexdigest(),
        "queries_sha256": sha256(queries_path.read_bytes()).hexdigest(),
        "config": {"chunk_max_chars": max_chars, "overlap_line_pieces": 1, "top_k_documents": top_k, "rrf_k": 60, "candidate_depth": 50},
        "counts": {"documents": len(sources), "chunks": len(chunks), "dev": len(dev), "test": len(test), "test_answerable": sum(bool(q["relevant"]) for q in test)},
        "methods": {},
    }
    for method in METHODS:
        threshold, dev_metrics = select_threshold(retriever, dev, method)
        metrics_rows, details, latencies = [], [], []
        for query in test:
            start = time.perf_counter()
            # Overfetch all chunks before document dedup: @k denotes k documents.
            hits = retriever.search(query["query"], method=method, top_k=len(chunks))
            ans = answer(retriever, query["query"], method=method, threshold=threshold)
            latencies.append((time.perf_counter() - start) * 1000)
            ranking = document_ranking(hits)
            row = retrieval_metrics(ranking, query["relevant"], top_k) if query["relevant"] else None
            if row:
                metrics_rows.append(row)
            details.append({**query, "ranking": ranking[:top_k], "metrics": row, "answer": ans.to_dict()})
        test_cls = classification_metrics([bool(q["relevant"]) for q in test], [not d["answer"]["abstained"] for d in details])
        result["methods"][method] = {
            "threshold": threshold, "dev_abstention": dev_metrics,
            "retrieval": {key: mean(row[key] for row in metrics_rows) for key in metrics_rows[0]},
            "test_abstention": test_cls,
            "latency_ms": {"median": float(np.median(latencies)), "p95": float(np.percentile(latencies, 95)), "scope": "two searches per query; local warm index; not a service SLA"},
            "queries": details,
        }
    return result
