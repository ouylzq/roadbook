# todo-reset 路书
> 最后勘路：2026-09-09，对应环境 demo-app（http://localhost:4173，`preview_start {name:"demo"}` 起）

## 全局约定

- 有打字步骤，全程 `resize_window preset=desktop`，不钉视口。
- 每次点击前重新截图，只用最新那张图的坐标。

## 步骤

1. 【参考】add-task
   【目的】造数：让列表非空
   【锚点】顶部输入框（placeholder「需要做什么？」）和右侧蓝色按钮「添加任务」
   【动作】点输入框 → 输入「待清空」→ 点「添加任务」
   【到位标志】列表出现「待清空」，header「未完成 1」

2. 【参考】reset-demo-data
   【目的】重置
   【锚点】任务卡片下方描边按钮「重置演示数据」
   【动作】点它，等 1 秒
   【到位标志】列表显示「还没有任务。」

3. 【参考】—
   【目的】写操作后回读
   【锚点】当前 URL
   【动作】navigate 到同一 URL，等 2 秒，`get_page_text`
   【到位标志】仍是「还没有任务。」

4. 【参考】—
   【目的】给裁判留事实，然后交棒
   【锚点】—
   【动作】写 `runs/<本次>/context.yaml`（seeded_title）；按 SKILL.md 第 6 步新起裁判；跑
     `scripts/judge.py scenarios/todo-reset runs/<本次>`
   【到位标志】`runs/<本次>/judgment.yaml` 出现，judge.py 给出退出码
