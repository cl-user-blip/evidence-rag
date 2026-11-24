# 混合检索 / Hybrid retrieval

本资料是原创演示语料中的工程约定，不代表真实公司的内部制度。
BM25 采用词项频率、逆文档频率和长度归一化；它适合错误码、版本号等精确匹配。英文词项与中文二元字串用于无分词器的词法基线。
Character TF-IDF 对字符二至四元组建立向量，L2 归一化后的点积即 cosine similarity。它有助于部分拼写与中文短语匹配，但不能理解同义词的语义。
Reciprocal Rank Fusion (RRF) 按各路名次累加 1 / (60 + rank)，避免直接相加 BM25 与 cosine 的异尺度分数。这里的 60 是固定实验参数，不是最优值结论。
每路只融合前 50 个正分候选。离线评测对重复来源去重，Recall@3 的 3 指三个不同文档，不是三个相邻切块。

## Failure modes
Two sparse retrievers can make correlated mistakes. RRF is not guaranteed to improve every query. Neither branch uses a neural embedding model or a learned reranker.
