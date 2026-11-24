# 证据不足与拒答 / Abstention

离线系统用最高排名片段的字符 cosine 作为证据相似度启发值。这不是概率，也不是事实蕴含检测。
只在 dev 集上选择拒答阈值，目标先最大化 balanced accuracy，再以 F1 打破平局。test 集只报告结果，不能反过来用于调阈值。
未知问题包括完全无关的问题，也包括主题相关但资料没有覆盖的细节。后者更难：提及 Redis 的片段不能回答 Redis 所在机房。
拒答要与检索分开评测：有答案问题计算 Recall、MRR、nDCG；全部测试问题计算拒答混淆矩阵及 unknown false accept rate。
上线前需要人工标注真实问题，补充同主题无答案样本，再检验阈值迁移。小型手写语料的高分不是生产质量保证。

## Product wording
When evidence is weak, say that the corpus does not contain sufficient support. Do not turn the model's confidence or retrieval score into a guarantee.
