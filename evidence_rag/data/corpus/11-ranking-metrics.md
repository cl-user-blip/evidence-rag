# 检索指标 / Ranking metrics

Recall@k 衡量前 k 个不同文档覆盖了多少相关文档。多个 chunk 命中同一来源不能重复计算 recall。
MRR@k 只看第一个相关文档的倒数排名，没有命中时为零。它不刻画后续多个相关结果的覆盖。
nDCG@k 按排名折扣累积相关性，再除以理想排序的分数。本项目使用二值相关标签，没有声称做 graded relevance 标注。
无答案问题不参与 Recall、MRR 与 nDCG 的平均，单独参与拒答评测；把它们当成 recall 为一会虚增指标。

## Example
If the only relevant document is ranked second, Recall@3 is 1, MRR@3 is 0.5 and nDCG@3 is 1/log2(3). Duplicate chunks from one file are deduplicated before evaluation.
