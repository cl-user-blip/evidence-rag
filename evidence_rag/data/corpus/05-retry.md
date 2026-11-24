# 重试与幂等 / Retry and idempotency

临时错误使用有上限的指数退避，并增加 jitter 避免并发客户端同时重试。确定性参数错误不应无条件重试。
HTTP 429 可以在请求预算允许时依据服务端 Retry-After 等信息安排重试；具体服务行为仍需查询对应接口文档。
对扣款或发邮件等有副作用的操作使用 idempotency key。幂等键绑定逻辑操作，同一步重试复用该键，不能每次新建随机键。
重试次数与总时长都应计入预算。日志记录 attempt、error category、delay 和最终状态，便于区分工具故障与规划错误。

## Boundary
This fixture does not specify any vendor's maximum retry count, prices, throughput quota, or commercial SLA.
