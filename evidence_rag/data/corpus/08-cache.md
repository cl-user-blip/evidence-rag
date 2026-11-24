# 缓存一致性 / Cache invalidation

检索索引缓存键至少包含语料摘要、切块配置、分词规则与向量化配置。只按目录名缓存会返回过期结果。
答案缓存还要绑定 query、检索方法、top_k 和拒答阈值；若存在用户权限，必须把权限域加入缓存键，避免跨租户泄露。
缓存命中率不等于正确率。报告需要区分冷启动建索引耗时与热索引查询延迟。
Redis 在这里只是可选缓存示例，资料没有提供实际 Redis 地址、密码、部署机房或实例规格。

## Tradeoff
Immutable content-addressed cache entries make invalidation explicit but require a retention policy. An experiment report should state whether timings include indexing.
