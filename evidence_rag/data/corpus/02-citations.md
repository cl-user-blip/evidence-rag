# 引用溯源 / Source citations

检索切块保留相对文件名、起止行号和内容摘要生成的稳定 chunk ID。引用形式为 filename.md:L2-L7，必须能回到原文。
文件名与行号相同但内容发生修改时，chunk ID 也会改变。移动文件会改变 ID；这个取舍优先保证可复现性，不保证跨重构的永久标识。
抽取式回答直接展示原文片段和引用，不用语言模型改写。引用存在仅能证明片段来自该文件，不能证明它回答了用户问题。
如果接入生成模型，应额外检查引用 ID 是否在检索候选内，并评估每个事实的证据支持；仅做引用格式校验不足以防止幻觉。

## Versioning
Record corpus and query SHA256 digests in every report. Changes to the corpus invalidate old line references. Keep source revision and report together when discussing an experiment.
