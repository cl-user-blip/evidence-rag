# Evidence RAG

**面向面试讲解的检索与证据实验：双路稀疏检索、逐行引用、独立 query dev/test、可展开的失败案例。**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/License-MIT-087e80)

![实测检索指标与引用预览](docs/preview.svg)

这个项目关注 RAG 最容易被“能聊天”掩盖的问题：**相关文档能否稳定找回、引用能否回溯、资料没有答案时会发生什么。** 默认完全离线，使用 BM25、字符 TF-IDF 和 RRF；回答直接摘录原文，不调用大模型。字符 TF-IDF 不是语义 embedding，当前版本也没有神经重排器。

## 3 分钟运行

```bash
git clone https://github.com/cl-user-blip/evidence-rag.git
cd evidence-rag
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m evidence_rag evaluate --output outputs
python -m evidence_rag query "How does reciprocal rank fusion combine retrieval rankings?"
python -m pytest
```

直接用浏览器打开 `outputs/report.html`；里面可以展开全部 RRF 测试问题，看源文档、真实片段、分路分数和误拒／误接收。GitHub 文件页不直接渲染 HTML：可下载已生成的 [examples/report.html](examples/report.html) 后打开，或本地运行上面的命令。[完整机器可读结果](examples/metrics.json) 也已提交。

没有 API Key、付费模型调用或外部语料下载；内置资料为本项目原创。安装 Python 依赖需要网络。

## 评测结果

以下来自提交的 `examples/metrics.json`，环境 Python 3.14.6、NumPy 2.4.6、scikit-learn 1.9.0。本地测试通过 18 项，1 项因 Windows 符号链接权限跳过。随本地交付提供 Python 3.11/3.12 CI 配置，当前未发布至远端，需要额外 workflow 授权；尚无远程 CI 结果。

| 排序方法 | Recall@3 ↑ | MRR@3 ↑ | nDCG@3 ↑ | 拒答 balanced accuracy ↑ | 未知问题误接收率 ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | 0.933 | 0.967 | 0.924 | 0.667 | 0.667 |
| Character TF-IDF | 0.933 | 0.933 | 0.899 | 0.550 | 0.500 |
| RRF | 0.933 | 0.967 | 0.924 | 0.550 | 0.500 |

实验规模：12 篇原创双语资料、25 个切块；12 个 dev 问题；21 个 test 问题，其中 15 个有答案、6 个无答案。`@3` 指去重后的前三个**不同文档**。无答案问题不参与排序指标的平均，另参与拒答混淆矩阵。

**RRF 在这组问题上没有超过 BM25；高 recall 也没有解决拒答。** RRF 对 6 个无答案问题仍误接收了 3 个，对 15 个有答案问题误拒了 6 个。比如“checkpoint 数据库密码是什么？”会命中讲 checkpoint 的资料，相似度很高，但语料没有密码。这正是检索相似度与事实支持之间的差别。报告保留这些失败，没有只展示成功问题。

阈值分别按每个方法的 dev balanced accuracy、F1、更高阈值的顺序选择，test 不参与阈值选择。默认 CLI query 使用手工阈值 `0.16`；复现当前 RRF 评测的决策可传 `--threshold 0.1679944167`。这个分数是余弦相似度启发值，**不是置信概率**。

这套语料和 qrels 均为人工编写的小规模演示，dev/test 属于同一作者、同一资料范围；不是独立公开基准，也不是生产 A/B 测试。320 字符预算用于让资料实际分成多个可追溯片段，没有做 chunk-size 超参数搜索。不能从这张表推断在真实客服、企业知识库或不同语言上的效果。

## 做了哪些工程工作

- **可追溯切块**：UTF-8 Markdown → 有界长度切块 → 相对路径、原始行号、内容相关稳定 ID；支持单行超长内容和重叠，忽略语料根外的符号链接。
- **可解释检索**：英文词项 + 中文二元字串 BM25、2–4 字符 TF-IDF、固定深度 RRF；保留每路分数，避免直接混加不同量纲。
- **可检查证据**：输出原文片段和 `file.md:Lx-Ly` 引用；报告中不把“引用存在”当成“答案正确”。
- **可复现评测**：dev 选阈值、test 报告排序与拒答；记录语料摘要、问题摘要、版本和配置。测试会修改 test 标签并验证 dev 阈值不变。
- **可浏览交付**：不依赖 CDN 的独立 HTML 报告、JSON 原始结果、GitHub SVG 预览、CI 与边界测试。

```mermaid
flowchart LR
  A[Markdown] --> B[带行号切块]
  B --> C[BM25]
  B --> D[字符 TF-IDF]
  C --> E[RRF]
  D --> E
  E --> F[dev 阈值与原文抽取]
  F --> G[逐行引用]
  E --> H[独立 test 指标]
  G --> I[HTML / JSON 报告]
  H --> I
```

## 换成自己的资料

```bash
python -m evidence_rag ingest ./my-docs --output outputs/chunks.json
python -m evidence_rag query "你的问题" --corpus ./my-docs --method rrf --json
python -m evidence_rag evaluate --corpus ./my-docs --queries ./queries.json --output outputs/my-data
```

自定义 `queries.json` 格式如下；正式评测应包含 dev/test，dev 同时包含有答案与无答案问题，所有相关文件路径相对语料根目录。不要把公司的私密资料提交到公开仓库。

```json
[
  {"id":"dev-1","split":"dev","query":"相关问题","relevant":["guide.md"]},
  {"id":"dev-2","split":"dev","query":"资料没覆盖的问题","relevant":[]},
  {"id":"test-1","split":"test","query":"另一个相关问题","relevant":["guide.md"]}
]
```

修改 chunk 长度可加 `--max-chars 240`；检索指标的 `--top-k` 表示不同文档数，query 的 `--top-k` 表示返回候选切块数。用自己的语料时应重新在 dev 选阈值，不能直接套用演示资料的数值。

## 适合讲清楚的取舍

1. 为什么先实现可解释的稀疏基线，而不是一开始就依赖向量数据库？
2. 为什么按文档去重后再算 Recall，为什么不把无答案问题混进平均值？
3. RRF 为什么可能无收益？为什么拒答阈值在 dev 有效、在 test 失效？
4. 引用完整性、证据蕴含和答案正确性之间分别缺了哪一步？
5. 从内存扫描扩展到百万文档，需要哪些索引、权限、更新和评测改造？

见 [实现设计与复杂度](docs/design.md) 和 [面试讲解与追问](docs/interview.md)。这是可复现的个人工程实验，不能当作已有线上业务经验或实际业务收益。

## 参考

- [scikit-learn TfidfVectorizer 官方文档](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)：字符分析器、n-gram 和 L2 归一化。
- [Cormack, Clarke & Büttcher, SIGIR 2009 作者版本](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf)：RRF 方法。论文中的效果不代表本项目实验结果。
- [Robertson & Zaragoza, 2009](https://doi.org/10.1561/1500000019)：BM25 与概率相关框架。

MIT License。语料为原创工程教学材料，包含简化策略与明确的实验边界。
