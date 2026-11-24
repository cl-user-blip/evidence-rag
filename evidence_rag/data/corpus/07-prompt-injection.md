# 提示注入 / Prompt injection

检索文档和工具返回值属于不可信数据。文档里出现“忽略系统规则”不能获得执行工具或导出密钥的权限。
Prompt injection 不能只靠在 prompt 中写一句警告解决。工具层要实施允许列表、参数校验和最小权限，规划模型不能绕开这些边界。
网页文本中嵌入的工具调用样式只是数据。对外发送内容需要单独授权，工具结果不能替用户授权。
评测应包含直接越权请求、间接文档注入和正常任务，分别记录拒绝率与正常任务完成率，防止通过全部拒绝获得虚假的安全成绩。

## Scope
This note describes an engineering boundary, not a claim that the portfolio code is immune to all prompt injection attacks.
