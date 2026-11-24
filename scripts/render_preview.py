"""Create a GitHub-native SVG preview from the committed experiment artifact."""

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
result = json.loads((ROOT / "examples/metrics.json").read_text(encoding="utf-8"))
rows = []
for i, (method, item) in enumerate(result["methods"].items()):
    y = 290 + i * 62
    values = list(item["retrieval"].values())
    rows.append(f'<rect x="54" y="{y - 29}" width="1092" height="52" rx="7" fill="{"#e7f3ee" if method == "rrf" else "#f3f6f4"}"/><text x="75" y="{y}" font-size="18" font-weight="650">{method.upper()}</text>')
    rows.extend(f'<text x="{x}" y="{y}" font-size="21" font-weight="600">{value:.3f}</text>' for x, value in zip([430, 650, 870], values))
counts = result["counts"]
false_accept = result["methods"]["rrf"]["test_abstention"]["false_accept_rate"]
citation = result["methods"]["rrf"]["queries"][0]["answer"]["hits"][0]["citation"]
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-labelledby="title desc">
<title id="title">Evidence RAG retrieval and source citation preview</title><desc id="desc">Actual small-fixture test metrics, RRF citation example, and abstention limitation.</desc>
<rect width="1200" height="720" rx="16" fill="#f5f6f2"/>
<rect x="0" y="0" width="1200" height="173" rx="16" fill="#143a40"/><rect x="0" y="145" width="1200" height="28" fill="#143a40"/>
<g font-family="Segoe UI,Arial,Microsoft YaHei,sans-serif" fill="#17333d">
<text x="54" y="44" fill="#80d5c6" font-size="12" font-weight="700" letter-spacing="3">SPARSE RETRIEVAL / SOURCE EVIDENCE / EVALUATION</text>
<text x="54" y="103" fill="#ffffff" font-size="47" font-weight="750">Evidence RAG</text>
<text x="54" y="143" fill="#c6dedd" font-size="18">可追溯检索 · 原文抽取基线 · 逐题检查失败</text>
<text x="795" y="102" fill="#ffffff" font-size="17">{counts['documents']} docs / {counts['chunks']} chunks</text>
<text x="795" y="136" fill="#c6dedd" font-size="15">{counts['dev']} dev / {counts['test']} test queries</text>
<text x="55" y="213" font-size="13" fill="#65808a" font-weight="650">01  /  DOCUMENT-LEVEL TEST RETRIEVAL</text>
<text x="75" y="248" font-size="12" fill="#65808a">METHOD</text><text x="430" y="248" font-size="12" fill="#65808a">RECALL@3</text><text x="650" y="248" font-size="12" fill="#65808a">MRR@3</text><text x="870" y="248" font-size="12" fill="#65808a">NDCG@3</text>
{''.join(rows)}
<rect x="54" y="459" width="665" height="151" rx="9" fill="#ffffff" stroke="#d2e0da"/>
<text x="76" y="490" fill="#087e80" font-size="12" font-weight="700">02 / INSPECTABLE EVIDENCE</text>
<text x="76" y="524" font-size="17" font-weight="600">{escape(citation)}</text>
<text x="76" y="557" font-size="15">Reciprocal Rank Fusion: sum 1 / (60 + rank)</text>
<text x="76" y="586" fill="#65808a" font-size="13">来源、行号、分路分数、原文片段均可在 HTML 展开。</text>
<rect x="739" y="459" width="407" height="151" rx="9" fill="#fff0da"/>
<text x="761" y="490" fill="#a96824" font-size="12" font-weight="700">03 / KNOWN LIMITATION</text>
<text x="761" y="536" fill="#a96824" font-size="34" font-weight="750">{false_accept:.0%}</text>
<text x="859" y="533" fill="#80572c" font-size="14">未知问题误接收率</text>
<text x="761" y="573" fill="#80572c" font-size="14">相关片段 ≠ 问题已有答案</text>
<text x="54" y="657" fill="#65808a" font-size="14">原创小型语料；结果不代表生产效果。RRF 本次与 BM25 持平；拒答仍需改进。</text>
<text x="54" y="687" fill="#65808a" font-size="12">RUN: python -m evidence_rag evaluate --output outputs    /    OPEN: outputs/report.html</text>
</g></svg>'''
(ROOT / "docs/preview.svg").write_text(svg, encoding="utf-8")
print("Generated docs/preview.svg from examples/metrics.json")
