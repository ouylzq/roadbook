# todo-complete 路书
> 最后勘路：2026-09-09，对应环境 demo-app（http://localhost:4173，`preview_start {name:"demo"}` 起）

## 全局约定

- 有打字步骤，全程 `resize_window preset=desktop`，不钉视口。
- 每次点击前重新截图，只用最新那张图的坐标。

## 步骤

1. 【参考】reset-demo-data
   【目的】从零开始
   【锚点】任务卡片下方描边按钮「重置演示数据」；列表若已是「还没有任务。」则跳过
   【动作】点它
   【到位标志】列表显示「还没有任务。」

2. 【参考】add-task
   【目的】加两条
   【锚点】顶部输入框（placeholder「需要做什么？」）和右侧蓝色按钮「添加任务」
   【动作】重复两次：点输入框 → 输入 intent.md 里的第 N 个标题 → 点「添加任务」；每加一条等它出现再加下一条
   【到位标志】列表两条，header「未完成 2」

3. 【参考】toggle-done
   【目的】把第一条标成已完成
   【锚点】第一条任务最左边的复选框（`read_page` 里是 checkbox「切换 完成演示 1」）
   【动作】点它，等 1 秒
   【到位标志】header 变「未完成 1」——**看计数器，不看复选框**，勾选状态文本层读不到

4. 【参考】—
   【目的】写操作后回读
   【锚点】当前 URL
   【动作】navigate 到同一 URL，等 2 秒，`read_page` 读 header
   【到位标志】两条标题都在，header 仍是「未完成 1」

5. 【参考】—
   【目的】给裁判留事实，然后交棒
   【锚点】—
   【动作】写 `runs/<本次>/context.yaml`（task_titles、done_title）；按 SKILL.md 第 6 步新起裁判；跑
     `scripts/judge.py scenarios/todo-complete runs/<本次>`
   【到位标志】`runs/<本次>/judgment.yaml` 出现，judge.py 给出退出码
