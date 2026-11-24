# Agent 预算 / Execution budget

一个运行同时限制最大步骤数、总墙钟时间和工具调用数。每次调用前检查剩余额度，避免规划循环无界增长。
硬预算耗尽时终止为 budget_exceeded，保留已完成步骤的记录，返回可解释的停止原因。不能偷偷扩大预算继续执行。
Token usage 与费用需要由实际接口返回值或明确费率计算。离线演示不应把字符数假装成真实 token 消耗。
预算限制不等价于安全策略：即使预算充足，越权文件读取和未经授权的外部写入仍然应被拒绝。

## Observability
Trace events should distinguish planning, tool execution, retries, budget checks and finalization. Aggregate latency hides which stage exhausted the budget.
