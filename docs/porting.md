# 换别的浏览器工具怎么接

这套设计不绑定任何一套浏览器工具。做法是把资产和工具分成两层，规矩写在
[`references/runtime-contract.md`](../references/runtime-contract.md)：

- **资产层**（`scenarios/`、`atoms/`）只说能力名——看画面、读页面文本、按引用点、打字……
- **运行时层**（`references/runtimes/<名字>.md`）把每项能力绑到具体工具，并收录那套工具专属的坑

**接一套新的 = 写一个 `references/runtimes/<名字>.md`**，照现有两份的「能力绑定」表格式填，
再把该运行时特有的坑写进去。资产层一个字不用改，`SKILL.md` 不用改，linter 也不用改——
`tests/lint_atoms.py` 的禁用词表是从运行时文件里自动提取的，新工具名自动被纳入拦截。

## 记忆层：你的运行时给不给

能力词表里有两项不是浏览器能力：「提议原子」「给候选投票」。它们对应的是原子的写入规则
（`atoms/README.md`「谁能写」）：已有原子的改动要经另一次跑批验证才落盘，全新原子直写，
「它长什么样」只由人改。

- **运行时有记忆层**（收候选、注入后续任务、数票、落盘、记账本）：把这两项绑成工具，
  并且**不要给 agent 任何能写 `atoms/` 的工具**——规则由代码卡住。
- **没有**：这两行写「没有记忆层，直接编辑文件」，agent 自己守规则。

两种运行时跑出来的 `atoms/` 应该长得一样。`references/runtime-contract.md`「记忆层」有那张对照表。

现成的两份：
[`runtimes/claude-pane.md`](../references/runtimes/claude-pane.md)（Claude Code 桌面版内置 pane）、
[`runtimes/playwright-mcp.md`](../references/runtimes/playwright-mcp.md)（无头容器 / CI）。

## 协议真正需要的能力

除了词表里那些，还有一项不属于浏览器、但裁判分离依赖它：

| 能力 | 协议为什么需要它 | Claude Code | Playwright MCP | Midscene |
|---|---|---|---|---|
| 起一个上下文干净的第二个 agent | 裁判分离 | `Task` 工具 | 自己编排 | 自己编排 |

替换时的几处注意：

- **用无障碍树快照代替页面文本。** Playwright MCP 的 snapshot 比纯文本信息更多，
  当证据通道完全可用——但它更啰嗦，也更容易随版本变化。
  引用时窄一点，并且坚持**引用**而不是概括。
- **用 `aiQuery` 之类的结构化抽取代替自己读文本。** 可以，但**不要**把裁判换成一个
  返回布尔值的自然语言断言——那会去掉原文证据，而原文证据正是让判决可复核的那部分。
- **拿不到第二个 agent 的情况。** 那么分离只能靠流程而不是结构：把裁判跑成一个独立进程、
  上下文干净、只交给它 `expect.yaml` 和 `context.yaml`。这比数据流保证弱——同一个会话
  评判自己的成果会漂向自我确认——所以要在报告里说明这一点。
- **拿截图当证据。** 别。这套设计存在的全部原因就是"像素是对的，数据是错的"。

`scripts/judge.py` 完全没有浏览器依赖。它只读两个 YAML、给一个退出码，可以原样移植。

## Headless / CI

跑通了。形状是**三棒**，不是一个 agent 从头干到尾：

```bash
# 第一棒：runner。回放路书、写完 runs/<本次>/context.yaml 就停，它不判。
claude -p "/roadbook <场景>" --bare --add-dir <repo> \
  --mcp-config mcp.json \
  --allowedTools "mcp__playwright,Read,Write,Edit,Glob,Grep,Bash(python3 *)" \
  --permission-mode dontAsk --max-turns 200 --output-format json

# 第二棒：裁判。**全新进程、上下文干净**，只给协议 + expect.yaml + context.yaml。
claude -p "你是裁判。照 references/judge-protocol.md 执行，产出 <run>/judgment.yaml。
场景验收路线：scenarios/<场景>/expect.yaml
本次事实：<run>/context.yaml
被测环境：<域名>
每一屏你自己加载，证据引页面原文；evidence/note/how 一律用块标量 |- 。
你不读路书、不读原子。" --bare --add-dir <repo> --mcp-config mcp.json \
  --allowedTools "mcp__playwright,Read,Write,Bash(python3 *)" \
  --permission-mode dontAsk --max-turns 120 --output-format json

# 第三棒：记分。
python3 scripts/judge.py scenarios/<场景> <run>
```

两个进程比一个 subagent 的隔离**更彻底**：各自的上下文从头就是干净的。

`mcp.json` 指向 `playwright-mcp --headless --caps=vision --user-data-dir <目录>`。
**别用 `--isolated`**：裁判是另起的进程、另开的浏览器，profile 跑完即焚的话它是未登录态，
而协议要求它自己加载每一屏。两棒先后跑，不争同一份 profile。

几个实测踩过的坑：

- **`--bare` 要带，但要知道代价。** 带上只有 Bash / 文件读 / 文件改三个工具，**没有 `Task`**，
  起不了 subagent——所以裁判才拆成上面的第二棒。不带 `--bare` 的话工具变成 27 个，
  加上可访问树快照的体积，实测会让 autocompact 反复抖动、整个 run 挂掉。
- **MCP server 要预装成可执行文件，别靠 `npx` 现拉。** Claude Code 2.1.221 之前
  不会等 pending 的 MCP server 就绪，`npx` 冷启动会让第一轮抢跑——agent 报告
  "我没有浏览器工具"，看起来像配置错了，其实是竞态。
- **`claude -p` 的退出码不是测试结论。** 它只说明 agent 跑完了。结论在
  `runs/<本次>/verdict.txt`，由 `judge.py` 写；CI 要读那个文件来判红绿。
- **无头模式下没人能接管。** 任何"等人处理"的分支（人机验证、需要人点确认）
  都应该直接 BLOCK，而不是等待。

一次实测的量级（一条登录场景，真实产品，走一个 LLM 网关）：
runner 5.4 分钟 / 54 轮，裁判 4.3 分钟 / 36 轮，合计约 10 分钟，判决 PASS。
