# 时序数据划分 / Temporal split

时序预测按时间先后划分训练、验证和测试，不使用随机打乱后的切分。用未来信息拟合标准化器会造成数据泄漏。
多步预测的标签窗口可能跨越边界，必须按 forecast horizon 清除跨区间样本。仅仅让输入窗口按时间排序还不够。
模型与超参数只用训练和验证集选择，最终 test 留到方案确定后评估。逐时回测必须明确可用历史数据和更新时间。
特征工程也要遵守信息可用性：未来观测到的天气属于未来信息，已发布的天气预报则需要记录发布时间。

## Relation to retrieval
Retrieval's dev/test split is a query split, not a temporal split. Different tasks require different leakage checks.
