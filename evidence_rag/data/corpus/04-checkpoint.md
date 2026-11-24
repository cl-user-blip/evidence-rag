# Agent 断点 / Checkpoints

演示工作流在每个已完成工具步骤后保存状态快照，字段包括 run_id、step、输入摘要、工具结果和状态版本。
恢复时只推进未完成步骤。工具具有外部副作用时，必须使用幂等键或核对执行记录；仅靠恢复快照不能保证 exactly-once。
Checkpoint replay means resuming a workflow from persisted state. It is different from replaying every API request blindly.
状态升级要有 schema version 和迁移函数；无法识别的新版本应明确失败，不能静默丢弃字段。

## Storage boundary
此演示资料不规定 checkpoint 数据库产品、版本、机房、云厂商或连接密码。持久化方案应根据并发与一致性要求选择。
