# 原子状态账本

> 由 `scripts/atoms_status.py` 生成，**别手改**。状态只来自 PASS 的 run，不是谁觉得它验过了。
> 生命周期：30 天没被 PASS run 经过记陈旧，90 天记归档候选；只归档不删。
> 依据：0 个 PASS run，7 份路书，3 个原子。

| 原子 | description | 状态 | 最近验证 | 被哪些路书引用 |
|---|---|---|---|---|
| `add-task` | 演示应用「任务列表」的新增入口：顶部输入框加右侧「添加任务」按钮，输入标题提交后列表多一条、计数器加一。点不进输入框、打不了字、加完刷新就没了时来查。 | 已引用，未验证 | — | todo-batch-add、todo-complete、todo-persistence、todo-reset |
| `reset-demo-data` | 演示应用「任务列表」的清空按钮：任务卡片下方描边的「重置演示数据」，点一下清掉存储里全部任务。场景要从零开始、或清理没清干净时来查。 | 已引用，未验证 | — | todo-batch-add、todo-complete、todo-persistence、todo-reset |
| `toggle-done` | 演示应用「任务列表」每条任务左侧的完成复选框：点一下标题加删除线、计数器减一。说不清勾上没勾上、或连勾几条丢了一条时来查。 | 已引用，未验证 | — | todo-complete |

汇总：已引用，未验证 3。
