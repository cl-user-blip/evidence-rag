# 使用与数据格式

## 环境与安装

Python 3.11 或更新版本，运行依赖为 NumPy 与 scikit-learn。建议使用独立虚拟环境：

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m evidence_rag --help
```

Windows PowerShell 中先执行 `.venv\Scripts\Activate.ps1`；macOS / Linux 中执行 `source .venv/bin/activate`。下文命令使用包内附带的语料作为默认输入，无需配置 API Key。

## 查询

```bash
python -m evidence_rag query "How does reciprocal rank fusion combine retrieval rankings?"
python -m evidence_rag query "checkpoint 如何恢复状态？" --method bm25 --top-k 5 --json
python -m evidence_rag query "缓存更新规则" --corpus ./my-docs --threshold 0.2 --json
```

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `question` | 必填 | 查询文本 |
| `--corpus` | 包内 `data/corpus` | Markdown 文档根目录 |
| `--method` | `rrf` | `bm25`、`tfidf` 或 `rrf` |
| `--threshold` | `0.16` | 排名第一的切块的字符 cosine 接受阈值，范围 `[0, 1]` |
| `--top-k` | `3` | 返回候选切块数，须大于零 |
| `--max-chars` | `320` | 切块字符预算，须不小于 80 |
| `--json` | 关闭 | 输出机器可读 JSON |

JSON 结果包含 `query`、`mode`、`abstained`、`confidence`、`threshold`、`passages` 与 `hits`。`passages` 最多包含两个原文片段；`hits` 包含本次返回的候选及其分数。拒答时 `passages` 为空，但仍保留候选用于检查。

`confidence` 是相似度启发值，不是模型置信概率。未检索到正分候选时，即使阈值为零也拒答。CLI 不会自动读取上一次评测选择的阈值；要复现某次评测，应从该次 `metrics.json` 取出阈值，显式传给 `--threshold`。

## 导出切块清单

```bash
python -m evidence_rag ingest ./my-docs --output outputs/chunks.json --max-chars 320
```

只读取根目录及其子目录内的 `.md` 文件，采用 UTF-8 解码，支持 BOM。根目录外的符号链接不加入语料。相邻切块重叠一个行片段，超长原始行按字符预算拆分，但继续保留原始行号。

导出文件是一个 JSON 数组，每个条目包含：

```json
{
  "id": "f46d8c3a0b4e2195",
  "source": "guide.md",
  "line_start": 1,
  "line_end": 5,
  "text": "原始文档片段"
}
```

上面是格式示例，不是实际计算出的 ID。ID 根据来源路径、行号和文本内容生成。切块清单用于来源审计，不是可以直接加载的持久检索索引；每次查询会从语料构建内存索引。

## 运行评测

```bash
python -m evidence_rag evaluate --output outputs/baseline
python -m evidence_rag evaluate --corpus ./my-docs --queries ./queries.json --top-k 5 --output outputs/custom
```

评测参数 `--top-k` 表示去重后的不同文档数；与 query 命令返回的切块数含义不同。默认评测 `@3`。

查询标签文件采用 JSON 数组：

```json
[
  {"id":"dev-known","split":"dev","query":"索引如何更新？","relevant":["guide.md"]},
  {"id":"dev-unknown","split":"dev","query":"文档未记录的值是什么？","relevant":[]},
  {"id":"test-known","split":"test","query":"更新操作的步骤","relevant":["guide.md"]},
  {"id":"test-unknown","split":"test","query":"当前服务器负载是多少？","relevant":[]}
]
```

- `id` 必须唯一；`split` 只能是 `dev` 或 `test`。
- `relevant` 中的路径必须相对语料根目录，并且对应存在的源文档；空数组表示语料不能回答该问题。
- dev 必须同时包含可回答与不可回答的问题，供阈值选择使用。
- test 至少包含一个可回答问题；要评估拒答的误接收率，也应加入独立的不可回答问题。
- 标签是文档级相关性，不表示相关文件的每个切块都完整回答问题。

每种方法分别在 dev 上选择阈值，再固定阈值评估 test。详细指标定义见 [设计文档](design.md#评测协议)。

## 输出文件

| 文件 | 内容 |
| --- | --- |
| `report.html` | 可离线浏览的排序指标、拒答统计与 RRF 逐题候选 |
| `metrics.json` | 三种方法的阈值、指标、查询明细、语料摘要、问题摘要、版本与配置 |
| `chunks.json` | ingest 命令导出的来源清单，文件名由 `--output` 指定 |

在浏览器中直接打开 `report.html`。报告不依赖 CDN 或外部 JavaScript，不会上传语料。公开发布报告前应检查原文片段与路径中是否包含私密内容。

## Python 接口

```python
from pathlib import Path

from evidence_rag.answer import answer
from evidence_rag.ingest import ingest
from evidence_rag.retrieval import Retriever

chunks = ingest(Path("my-docs"), max_chars=320)
retriever = Retriever(chunks)
hits = retriever.search("缓存更新规则", method="rrf", top_k=5)
result = answer(retriever, "缓存更新规则", threshold=0.2)
print(result.to_dict())
```

需要连续处理多个问题时复用同一个 `Retriever`，避免为每个问题重建索引。该接口没有隐式持久化、网络请求或异步后台任务。

## 错误与排查

输入目录不存在、语料为空、标签引用缺失文档、阈值或切块参数越界时，CLI 输出错误并以状态码 `2` 退出。出现检索结果但没有原文输出时，先检查 `abstained` 和阈值；出现高相似度误接收时，检查片段是否包含问题要求的属性，不能仅提高检索分数。
