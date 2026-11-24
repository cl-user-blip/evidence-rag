from copy import deepcopy
import json
import math

import pytest

from evidence_rag.cli import DATA, main
from evidence_rag.evaluate import classification_metrics, evaluate, retrieval_metrics


def test_metrics_known_ranking_and_deduplication():
    metrics = retrieval_metrics(["wrong.md", "wrong.md", "right.md"], ["right.md"], 3)
    assert metrics["recall@3"] == 1
    assert metrics["mrr@3"] == .5
    assert math.isclose(metrics["ndcg@3"], 1 / math.log2(3))
    assert retrieval_metrics(["a"], ["a", "b"], 3)["recall@3"] == .5
    with pytest.raises(ValueError):
        retrieval_metrics([], [], 3)


def test_abstention_is_evaluated_separately():
    metrics = classification_metrics([True, True, False, False], [True, False, True, False])
    assert [metrics[k] for k in ("tp", "fn", "fp", "tn")] == [1, 1, 1, 1]
    assert metrics["balanced_accuracy"] == .5
    assert metrics["false_accept_rate"] == .5


def test_test_labels_do_not_change_dev_threshold(tmp_path):
    original = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
    baseline = evaluate(DATA / "corpus", DATA / "queries.json")
    modified = deepcopy(original)
    for query in modified:
        if query["split"] == "test":
            query["relevant"] = ["01-retrieval.md"]  # Deliberately wrong test labels.
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(modified, ensure_ascii=False), encoding="utf-8")
    changed = evaluate(DATA / "corpus", path)
    for method in baseline["methods"]:
        assert baseline["methods"][method]["threshold"] == changed["methods"][method]["threshold"]
        assert baseline["methods"][method]["dev_abstention"] == changed["methods"][method]["dev_abstention"]
    assert baseline["methods"]["rrf"]["retrieval"] != changed["methods"]["rrf"]["retrieval"]
    assert baseline["counts"]["test_answerable"] == 15


def test_cli_report_contains_failures_and_no_external_assets(tmp_path):
    main(["evaluate", "--output", str(tmp_path)])
    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert "Redis 实例部署在哪个机房" in report
    assert "未知问题误接收率" in report and "<details>" in report
    assert "<script" not in report and "<link" not in report
    assert metrics["counts"]["documents"] == 12
    assert metrics["methods"]["rrf"]["test_abstention"]["fp"] > 0


def test_missing_relevance_source_rejected(tmp_path):
    queries = [{"id": "one", "split": "dev", "query": "missing", "relevant": ["missing.md"]}]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(queries), encoding="utf-8")
    with pytest.raises(ValueError, match="missing source"):
        evaluate(DATA / "corpus", path)
