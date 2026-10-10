---
name: reset-demo-data
description: 演示应用「任务列表」的清空按钮：任务卡片下方描边的「重置演示数据」，点一下清掉存储里全部任务。场景要从零开始、或清理没清干净时来查。
---

# reset-demo-data

## 它长什么样

任务列表页，任务卡片下方一个描边按钮「重置演示数据」。
点一下：列表变「还没有任务。」，header 计数器变「未完成 0」。
列表本来就空则什么都不用做。

## 变体

- 清掉 localStorage 的 `roadbook_demo_tasks` 键，效果等同。只在按钮找不到时用，并在路书里注明退守。

## 已知会失败的方式

- 导航之后按上一屏拿到的 ref 点它，报 `press at (0, 0)` → ref 绑定的是旧 DOM 节点，导航后全部过期 →
  重新搜一次再点
- pane 隐藏期间又导航了一次，ref 和坐标都点不动 → 隐藏时加载的页面没有排版 →
  对同一 URL `preview_start` 拉回 pane（会开新 tab），关旧 tab 再点；隐藏期间别导航

## 出处

- `scenarios/demo-app/todo-persistence/playbook.md` 第 1 步
