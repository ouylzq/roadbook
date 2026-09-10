# runner 过程记录（不是判据）

- 步 1：落地时列表已是「还没有任务。」，按路书跳过重置。
- 步 2：点输入框 → 输入「发布路书演示」→ 点「添加任务」。1 秒后 `get_page_text` 看到标题。
- 步 3：`navigate` 同一 URL，等 2 秒，文本仍有该标题，header「未完成 1」（在 `<main>` 之外，用 `read_page` 读到）。
  navigate 之后 `read_page` 报 `Viewport: 0x0`（pane 被隐藏，见 browser-pitfalls 第 3 条），文本工具照常可用。
- 步 4：写 context.yaml（只有 task_title），交棒。
