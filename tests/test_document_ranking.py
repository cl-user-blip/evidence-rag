from evidence_rag.evaluate import document_ranking, retrieval_metrics
from evidence_rag.ingest import Chunk
from evidence_rag.retrieval import Hit


def test_multiple_chunks_from_same_source_do_not_fill_document_slots():
    hits = [
        Hit(Chunk("1", "duplicate.md", 1, 2, "first"), 9, 8, .5),
        Hit(Chunk("2", "duplicate.md", 2, 3, "second"), 8, 7, .4),
        Hit(Chunk("3", "relevant.md", 1, 2, "third"), 7, 6, .3),
    ]
    ranking = document_ranking(hits)
    assert ranking == ["duplicate.md", "relevant.md"]
    metrics = retrieval_metrics(ranking, ["relevant.md"], k=2)
    assert metrics["recall@2"] == 1 and metrics["mrr@2"] == .5
