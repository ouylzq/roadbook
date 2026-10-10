# todo-persistence 路书
> 最后勘路：2026-09-09，对应环境 demo-app（http://localhost:4173，`preview_start {name:"demo"}` 起）

## 全局约定

- 这个应用有打字步骤，全程 `resize_window preset=desktop`，不钉视口。
- 每次点击前重新截图，只用最新那张图的坐标。

## 步骤

1. 【参考】reset-demo-data
   【目的】从零开始
   【锚点】任务卡片下方描边按钮「重置演示数据」；列表若已是「还没有任务。」则跳过
   【动作】点它
   【到位标志】列表显示「还没有任务。」

2. 【参考】add-task
   【目的】添加固定标题的任务
   【锚点】顶部输入框（placeholder「需要做什么？」）和右侧蓝色按钮「添加任务」
   【动作】点输入框 → 输入 intent.md 的固定标题 → 点「添加任务」
   【到位标志】列表出现该标题（`get_page_text` 可读），header 显示「未完成 1」

3. 【参考】—
   【目的】写操作后回读，确认存下来了而不是只渲染了
   【锚点】当前 URL
   【动作】navigate 到同一 URL，等 2 秒，`get_page_text`
   【到位标志】列表里仍有该标题；`?bug=optimistic` 模式下这里会变成「还没有任务。」——
     那就是这个演示要给你看的失败，照常往下走，让裁判去判

4. 【参考】—
   【目的】给裁判留事实，然后交棒
   【锚点】—
   【动作】写 `runs/<本次>/context.yaml`（只有 task_title，就是你实际输入的标题）；
     按 SKILL.md 第 6 步新起裁判 agent；跑
     `scripts/judge.py scenarios/demo-app/todo-persistence runs/<本次>`
   【到位标志】`runs/<本次>/judgment.yaml` 出现，judge.py 给出退出码
   ⚠️ runner 到这里就不再判断任何事。
