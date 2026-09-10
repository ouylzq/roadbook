# 换别的浏览器工具怎么接

`judge-protocol.md` 和 `browser-pitfalls.md` 里写的是 Claude Code 的浏览器工具名。
但这套设计不依赖它们——协议真正需要工具链提供的只有四项能力：

| 能力 | 协议为什么需要它 | Claude Code | Playwright MCP | Midscene |
|---|---|---|---|---|
| 导航到 URL，并能再加载一次 | 刷新正是"渲染出来了"和"存下来了"的分界线 | `navigate` | `browser_navigate` | YAML 步骤里的 `goto` |
| 读页面**文本** | 证据通道；`pass`/`fail` 必须引用它 | `get_page_text` | `browser_snapshot`（无障碍树） | 带 schema 的 `aiQuery` |
| 定位并点击 | 只用于驱动，永远不作证据 | `computer` 截图 + 坐标、`find`/ref | snapshot 的 ref | `ai` / `aiTap` |
| 起一个上下文干净的第二个 agent | 裁判分离 | `Agent` 工具 | 自己编排 | 自己编排 |

几处替换的注意事项：

- **用无障碍树快照代替页面文本。** Playwright MCP 的 snapshot 比纯文本信息更多，
  当证据通道完全可用——但它更啰嗦，也更容易随版本变化。
  引用时窄一点，并且坚持**引用**而不是概括。
- **用 `aiQuery` 代替自己读文本。** 如果你已经用 schema 抽结构化数据，
  那就用它做抽取、把比对留在 `judge.py` 里。
  **不要**把裁判换成一个返回布尔值的自然语言断言——那会去掉原文证据，
  而原文证据正是让判决可复核的那部分。
- **拿不到第二个 agent 的情况。** 那么分离只能靠流程而不是结构：
  把裁判跑成一个独立进程、上下文干净、只交给它 `expect.yaml` 和 `context.yaml`。
  这比数据流保证弱——同一个会话去评判自己的成果，会漂向自我确认——
  所以要在报告里说明这一点。
- **拿截图当证据。** 别。这套设计存在的全部原因就是"像素是对的，数据是错的"。

`scripts/judge.py` 完全没有浏览器依赖。它只读两个 YAML、给一个退出码，可以原样移植。

## Headless / CI

**没解决。** 现在 runner 和裁判都是交互式 agent 会话。
可行的形状是一个 Claude Agent SDK 程序：把两个阶段前后跑完、以 `judge.py` 的退出码退出、
把 `runs/<本次>/` 当构建产物。如果你把它做出来了，那正是这个仓库最需要的贡献。
