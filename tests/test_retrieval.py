import math

import pytest

from evidence_rag.answer import answer
from evidence_rag.ingest import Chunk
from evidence_rag.retrieval import Retriever, reciprocal_rank_fusion, tokenize


@pytest.fixture
def retriever():
    return Retriever([
        Chunk("a", "retry.md", 2, 3, "HTTP429 retry uses exponential backoff and jitter. 重试使用指数退避。"),
        Chunk("b", "budget.md", 4, 5, "ERR_BUDGET means execution budget exhausted. 预算耗尽后停止运行。"),
        Chunk("c", "forecast.md", 1, 2, "Forecast models use chronological temporal splits. 时序预测不能泄漏未来。"),
    ])


def test_exact_error_code_and_chinese_retrieval(retriever):
    assert retriever.search("ERR_BUDGET", "bm25")[0].chunk.source == "budget.md"
    assert retriever.search("指数退避", "rrf")[0].chunk.source == "retry.md"
    assert "预算" in tokenize("预算耗尽")


def test_rrf_uses_rank_and_not_input_scores():
    scores = reciprocal_rank_fusion([[2, 0], [1, 2]], k=60)
    assert math.isclose(scores[2], 1 / 61 + 1 / 62)
    assert scores[2] > scores[0] and scores[2] > scores[1]
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([[0]], k=-1)


def test_unknown_and_blank_queries_have_no_fabricated_answer(retriever):
    for text in ("", "   ", "zqxjkvv"):
        result = answer(retriever, text, threshold=0)
        assert result.abstained and not result.passages and not result.hits
        assert result.confidence == 0


def test_extracts_exact_passages_with_real_citations(retriever):
    result = answer(retriever, "HTTP429 retry", threshold=0)
    assert not result.abstained and result.mode == "offline-extractive"
    for passage in result.passages:
        chunk = next(c for c in retriever.chunks if c.id == passage["chunk_id"])
        assert passage["text"] == chunk.text
        assert passage["citation"] == chunk.citation
    assert answer(retriever, "HTTP429 retry", threshold=1).abstained


@pytest.mark.parametrize("method,top_k", [("dense", 3), ("rrf", 0)])
def test_invalid_search_settings(retriever, method, top_k):
    with pytest.raises(ValueError):
        retriever.search("query", method, top_k)


def test_empty_corpus_fails_clearly():
    with pytest.raises(ValueError, match="No nonempty"):
        Retriever([])
