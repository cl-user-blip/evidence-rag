"""A portable, escaped HTML report. No CDN, telemetry, or external JavaScript."""

from html import escape
import json
from pathlib import Path


def write_report(result: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows, cards = [], []
    for method, item in result["methods"].items():
        metrics, abstention = item["retrieval"], item["test_abstention"]
        rows.append(f"<tr><th>{escape(method.upper())}</th>" + "".join(f"<td>{value:.3f}</td>" for value in metrics.values()) +
                    f'<td>{abstention["balanced_accuracy"]:.3f}</td><td>{abstention["false_accept_rate"]:.3f}</td><td>{item["threshold"]:.4f}</td></tr>')
        bars = "".join(f'<div class="bar-row"><span>{escape(label)}</span><div class="track"><i style="width:{value * 100:.1f}%"></i></div><strong>{value:.3f}</strong></div>' for label, value in metrics.items())
        cards.append(f'<article class="metric-card"><span class="eyebrow">SPARSE RETRIEVAL</span><h2>{method.upper()}</h2>{bars}</article>')
    details = []
    for item in result["methods"]["rrf"]["queries"]:
        ans = item["answer"]
        expected = "有答案" if item["relevant"] else "无答案"
        status = "拒答" if ans["abstained"] else "返回原文"
        correct = bool(item["relevant"]) != ans["abstained"]
        evidence = []
        for hit in ans["hits"]:
            evidence.append(f'<div class="passage"><code>{escape(hit["citation"])}</code><span class="score">BM25 {hit["bm25"]:.2f} · cosine {hit["cosine"]:.3f}</span><pre>{escape(hit["text"])}</pre></div>')
        truth = "、".join(item["relevant"]) or "∅（资料没有覆盖问题所求）"
        details.append(f'<details><summary><span class="pill {"good" if correct else "bad"}">{expected} / {status}</span>{escape(item["query"])}</summary><div class="detail-body"><p>测试标签：{escape(truth)}<br>confidence={ans["confidence"]:.4f}，dev 选择的阈值={ans["threshold"]:.4f}；confidence 是相似度启发值。</p>{"".join(evidence) or "没有正分候选。"}</div></details>')
    k = result["config"]["top_k_documents"]
    counts = result["counts"]
    report = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Evidence RAG — Evaluation Report</title>
<style>
:root{{--ink:#172b38;--muted:#5e737e;--paper:#f5f6f2;--teal:#087e80;--line:#d7e0dc;--orange:#c57934}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 system-ui,-apple-system,"Segoe UI",sans-serif}}main{{max-width:1180px;margin:auto;padding:48px 26px 70px}}header{{border-top:5px solid var(--teal);padding-top:25px;position:relative}}.eyebrow{{font-size:11px;letter-spacing:2px;color:var(--teal);font-weight:750}}h1{{font-size:clamp(35px,6vw,66px);letter-spacing:-2px;line-height:1.1;margin:12px 0 16px}}h1 em{{font-style:normal;color:var(--teal)}}.intro{{max-width:760px;color:var(--muted);font-size:17px}}.tags{{display:flex;gap:10px;flex-wrap:wrap;margin:25px 0 32px}}.tags span{{border:1px solid var(--line);padding:5px 13px;border-radius:5px;background:white}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}.metric-card{{background:#fff;border:1px solid var(--line);padding:24px;border-radius:9px}}h2{{font-size:24px;margin:4px 0 20px}}.bar-row{{display:grid;grid-template-columns:80px 1fr 42px;gap:8px;align-items:center;font-size:12px;margin:13px 0}}.track{{height:7px;background:#e7eeee;border-radius:9px;overflow:hidden}}.track i{{display:block;height:100%;background:var(--teal)}}.notice{{margin:25px 0;padding:16px 22px;border-left:3px solid var(--orange);background:#fff6e9;color:#805827}}section{{margin-top:42px}}.table-wrap{{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:8px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:15px;text-align:left;border-bottom:1px solid var(--line)}}thead th{{color:var(--muted);font-size:11px;letter-spacing:.3px;white-space:nowrap}}.muted{{color:var(--muted);font-size:13px}}details{{margin:12px 0;border:1px solid var(--line);border-radius:7px;background:#fff}}summary{{cursor:pointer;padding:18px;list-style-position:inside;font-weight:600}}.pill{{display:inline-block;margin-right:12px;font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px}}.good{{background:#e3f3e9;color:#26734e}}.bad{{background:#fff0db;color:#9e6224}}.detail-body{{padding:0 22px 22px}}.passage{{margin:18px 0 0;background:#f5f8f7;border-radius:5px;padding:16px}}code{{color:var(--teal);font-size:12px}}.score{{float:right;font-size:11px;color:var(--muted)}}pre{{white-space:pre-wrap;font:13px/1.8 system-ui,sans-serif;margin:10px 0 0}}footer{{margin-top:45px;border-top:1px solid var(--line);padding-top:20px;font-size:12px;color:var(--muted)}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}main{{padding:28px 16px}}.score{{float:none;display:block}}}}
</style></head><body><main>
<header><span class="eyebrow">ALGORITHM × EVIDENCE × EVALUATION</span><h1>Retrieval you can <em>inspect.</em></h1><p class="intro">BM25 + 字符 TF-IDF + RRF。逐行保留证据，用独立 query test 集检查排序与拒答，直接展开失败案例。</p><div class="tags"><span>{counts["documents"]} 原创文档</span><span>{counts["chunks"]} 可追溯切块</span><span>{counts["dev"]} dev / {counts["test"]} test</span><span>无需 API Key · 全离线</span></div></header>
<div class="grid">{"".join(cards)}</div>
<div class="notice">实验边界：这是一套手工编写的小型双语工程资料和问题，dev/test 查询互不相同，但同属一个演示语料。结果用于验证实现与分析失败，不代表公开大规模基准或生产效果。回答是原文抽取，未调用大模型。</div>
<section><h2>01 / 同一语料，三种排序</h2><div class="table-wrap"><table><thead><tr><th>METHOD</th><th>RECALL@{k}</th><th>MRR@{k}</th><th>NDCG@{k}</th><th>拒答 BAL. ACC.</th><th>未知问题误接收率</th><th>DEV 阈值</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div><p class="muted">排序指标只在 {counts["test_answerable"]} 个有答案测试问题上平均；按不同源文档去重。拒答使用全部 {counts["test"]} 个测试问题。阈值按 dev balanced accuracy、F1 和更高阈值的顺序选择，test 未参与选择。</p></section>
<section><h2>02 / 展开 RRF 测试与证据</h2><p class="muted">绿色表示接受/拒答决策符合可回答性标签，不能据此认为完整回答正确。橙色显示误拒或误接收。检索出的片段即使带引用，也可能没有回答问题。</p>{"".join(details)}</section>
<section><h2>03 / 可复现记录</h2><p class="muted">Python {escape(result["versions"]["python"])} · NumPy {escape(result["versions"]["numpy"])} · scikit-learn {escape(result["versions"]["sklearn"])}</p><p class="muted">Corpus SHA256: <code>{result["corpus_sha256"]}</code><br>Queries SHA256: <code>{result["queries_sha256"]}</code></p><p>复现：<code>python -m evidence_rag evaluate --output outputs</code>。完整逐题排序、分数与混淆矩阵见同目录 <code>metrics.json</code>。</p></section>
<footer>EVIDENCE RAG / Original portfolio experiment · {escape(result["created_utc"])} · No external resources loaded.</footer>
</main></body></html>'''
    (output / "report.html").write_text(report, encoding="utf-8")
