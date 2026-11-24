import argparse
import json
from pathlib import Path
import sys

from .answer import answer
from .evaluate import evaluate
from .ingest import ingest
from .report import write_report
from .retrieval import METHODS, Retriever

DATA = Path(__file__).parent / "data"


def main(argv=None):
    # Keep Chinese output readable in redirected Windows terminals as well.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Offline, inspectable sparse retrieval with source citations")
    commands = parser.add_subparsers(dest="command", required=True)
    query = commands.add_parser("query", help="Retrieve exact source passages, with heuristic abstention")
    query.add_argument("question")
    query.add_argument("--corpus", type=Path, default=DATA / "corpus")
    query.add_argument("--method", choices=METHODS, default="rrf")
    query.add_argument("--threshold", type=float, default=.16, help="Manual heuristic threshold; evaluate selects one from dev")
    query.add_argument("--top-k", type=int, default=3)
    query.add_argument("--max-chars", type=int, default=320)
    query.add_argument("--json", action="store_true")
    evaluation = commands.add_parser("evaluate", help="Choose threshold on dev, then evaluate test")
    evaluation.add_argument("--corpus", type=Path, default=DATA / "corpus")
    evaluation.add_argument("--queries", type=Path, default=DATA / "queries.json")
    evaluation.add_argument("--output", type=Path, default=Path("outputs"))
    evaluation.add_argument("--top-k", type=int, default=3)
    evaluation.add_argument("--max-chars", type=int, default=320)
    ingestion = commands.add_parser("ingest", help="Export reproducible chunk manifest (no pickle)")
    ingestion.add_argument("corpus", type=Path)
    ingestion.add_argument("--output", type=Path, default=Path("outputs/chunks.json"))
    ingestion.add_argument("--max-chars", type=int, default=320)
    args = parser.parse_args(argv)
    try:
        if args.command == "query":
            result = answer(Retriever(ingest(args.corpus, max_chars=args.max_chars)), args.question, method=args.method, threshold=args.threshold, top_k=args.top_k)
            if args.json:
                print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(f"[offline-extractive] {args.method.upper()} | confidence={result.confidence:.4f} | threshold={result.threshold:.4f}")
                if result.abstained:
                    print("资料中的证据不足，拒绝给出推断答案。")
                else:
                    print("以下为检索原文，不是语言模型生成答案；引用存在不等于事实得到支持。")
                    for passage in result.passages:
                        print(f"\n[{passage['chunk_id']}] {passage['citation']}\n{passage['text']}")
        elif args.command == "evaluate":
            result = evaluate(args.corpus, args.queries, args.top_k, args.max_chars)
            write_report(result, args.output)
            for method, item in result["methods"].items():
                print(f"{method:6} " + " ".join(f"{key}={value:.3f}" for key, value in item["retrieval"].items()) + f" bal_acc={item['test_abstention']['balanced_accuracy']:.3f} unknown_false_accept={item['test_abstention']['false_accept_rate']:.3f} threshold={item['threshold']:.4f}")
            print(f"Report: {(args.output / 'report.html').resolve()}")
        else:
            chunks = ingest(args.corpus, max_chars=args.max_chars)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps([chunk.to_dict() for chunk in chunks], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Exported {len(chunks)} chunks to {args.output.resolve()}")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
