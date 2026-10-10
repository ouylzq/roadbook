# 路书 · Roadbook

**给 coding agent 用的 UI 主流程回归 Skill。** agent 照「路书」在真实浏览器里回放你的
应用；界面变了就自己勘路，勘完把路书改掉。**结论不由开车的那个 agent 给**——另起一个
**裁判** agent 按有序的验收路线走一遍，把读到的页面原文抄下来，再由一个一百多行的
记分器换算成退出码。

期望用人话写，只写一处——一步只有「去哪」和「看什么」两个键：

```yaml
goal: 在演示应用里加一个任务，确认它是真被存下来了，而不只是渲染出来

steps:
  - go: 打开任务列表 http://localhost:4173/ 并读取列表
    check:
      - 任务列表里正好有一条任务，标题是 context.task_title
      - header 里的计数器显示「未完成 1」

  - go: 打开统计视图 http://localhost:4173/?view=stats
    check:
      - 「总任务数」等于 1
      - 「未完成」等于 1
```

没有选择器，没有断言代码，也没有第二份需要同步的期望值。`context.*` 只引用 runner 跑的时候
才知道的东西（它实际输入的名字、新建对象的 id）；期望值直接写在这里，不由 runner 转述。

## 这是一套规范，不是一个工具

代码只有一百多行的记分器和三个索引脚本。这个仓库真正交付的是**一组约定**：文件放哪、写成什么样、
谁读谁不读、结论怎么算。任何照着这组约定跑的实现——换浏览器工具、换模型、换成 headless 程序——
产出的 run 都能互相比对、互相复核。规范一共八条，每条对应一份文件或一层目录：

| 规范 | 文件 | 定了什么 |
|---|---|---|
| 项目 | `scenarios/<项目>/` | 一个被测对象（产品/应用/站点）一个文件夹，一对多场景。只是分组不是命名空间：场景目录名全仓库唯一，换了项目也不许重名 |
| 场景 | `scenarios/<项目>/<名>/`（旧式平铺 `scenarios/<名>/` 仍然合法） | 三份文件：`intent.md`（frontmatter 一句话 + 人定边界，不写步骤）、`expect.yaml`、`playbook.md`。值不同就另开目录 |
| 期望 | `expect.yaml` | `goal` + 有序 `steps`，每步只有 `go` 和 `check` 两个键；`context.*` 只引用 runner 跑时才知道的事实，期望值写死 |
| 裁判 | `references/judge-protocol.md` | 独立 agent；每屏自己加载（唯一例外：加载就会消失的纯前端状态，且那一步不许断言后端事实）；证据引原文；找不到是 blocked 不是 fail；输出 `judgment.yaml` 按顺序与 expect 逐条对应，`fact` 逐字不改（`go` 不用抄） |
| 记分 | `scripts/judge.py` | 退出码 0 PASS / 1 FAIL / 2 BLOCK，只查完备与镜像，不碰语义 |
| 路书 | `references/exploration-rules.md` | 每步五要素【参考】【目的】【锚点】【动作】【到位标志】；agent **勘通一步就记一步**、进 git、失配即改写那一步；半份路书照样是资产——下次照着走到头再往前勘 |
| 原子 | `atoms/README.md` | agent 沉淀的产品节点记忆：frontmatter 一句话 + 它长什么样 + 现象→机制→对策；状态由 PASS run 推导。写入分两路：已有原子的改动要经**另一次跑批**验证才落盘，全新原子直写，「它长什么样」只由人改 |
| 运行时 | `references/runtime-contract.md` | 资产层只说能力名（看画面/读页面文本/按引用点…），工具名只许出现在 `references/runtimes/<名字>.md`；加一个运行时 = 加一个文件 |

贯穿七条的是一道**数据流墙**：runner 读 `intent.md`、`playbook.md`、`atoms/`，从不读 `expect.yaml`；
裁判读 `expect.yaml`、`context.yaml`，从不读路书和原子。裁判的独立性靠这道墙，不靠 prompt 里的"请客观"。

`tests/` 下四个检查就是这套规范的机器可读版本，CI 每次都跑。规范现在是 `v0.1`，
会随着接触更多产品而改——改了会在这一节和 `SKILL.md` 里同步写明。

## 为什么不能让模型看一眼截图就说「通过」

因为界面会骗人。这套东西所对的那个产品，同一个下午实测两次：

- 保存后界面弹「已保存」，后端还是旧值；
- 把数量从 4 改成 2，卡片显示 2、**概览面板也显示 2**，后端却仍是 4。真实数字直到最后的
  支付弹层才露出来——到那时操作者已经按错的金额确认了。

靠截图断言，这两次都会报 PASS。所以这个项目把通常被混为一谈的三件事拆开：

| | 谁做 | 怎么做 |
|---|---|---|
| 理解期望 | 模型 | 读一句人话 |
| 下判决 | 模型，但受协议约束 | 每条 `pass`/`fail` 必须引用读到的页面原文 |
| 给结论记分 | 代码 | 只查完备性，绝不碰语义 |

记分器从不比对数值。它只确认裁判把每一步都走了、每条都答了、每个答案都有原文兜底。
这才让一次 run 可复核、可跨次对比，而不是凭感觉。

## 让结论站得住的四条规则

1. **裁判不是司机。** 它是新起的 agent，没有操作上下文，也拿不到路书。这靠数据流强制，
   不靠 prompt 说"请客观"：runner 从不读 `expect.yaml`，裁判也从不读 `playbook.md`。
2. **每一屏都是裁判自己加载的。** 它绝不判读一个"到的时候就已经打开着"的页面——
   那可能是 runner 留下的、带着乐观渲染的那一屏。所以状态、数量、金额天然都是干净读
   到的值，上面两个 bug 都会现形。这是协议里的不变式，不是需要人逐步勾选的开关。
3. **证据必须原文引用。** 页面文本或接口原始值。"看着对"不算证据；`pass` 却没有证据，
   记分器判 BLOCK 而不是 PASS。
4. **BLOCK 是一等结论。** 环境坏了 ≠ 功能坏了。退出码 2 表示"无法判定"，
   而它成立的次数比大多数团队愿意承认的要多。

## 安装

需要带浏览器工具的 [Claude Code](https://claude.com/claude-code)、Python 3.10+ 和 PyYAML。

```bash
git clone https://github.com/ouylzq/roadbook.git
cd roadbook
pip install pyyaml

# 四项检查，都不需要浏览器
python3 tests/test_judge.py          # 记分器 14 个合成用例
python3 tests/test_examples.py       # 场景格式
python3 tests/lint_playbook.py       # 路书格式
python3 tests/lint_atoms.py          # 原子格式

# 装成用户级 skill（仓库根就是 skill 根）
ln -s "$PWD" ~/.claude/skills/roadbook
```

之后在任何项目里用 `/roadbook` 调起。

**目录约定**：`SKILL.md`、`references/`、`scripts/` 跟着 skill 走；`scenarios/`、`atoms/`、`runs/`
建在**被测项目**下。在本仓库里跑自带演示时两者是同一个目录，所以怎么写都对。

## 五分钟演示，含一次故意的失败

仓库自带一个演示应用——单个 HTML 文件、没有后端，可以先不指向生产就看完整闭环。

```
preview_start { "name": "demo" }        # 在 :4173 上跑 demo-app
/roadbook todo-persistence
```

场景自带一份 `playbook.md`，所以你看到的是**回放模式**：runner 照四步开、写 `runs/<本次>/context.yaml`、交棒。裁判自己走两步、抄原文，得到 `PASS`。
想看**探索模式**，把 `playbook.md` 删掉再跑一次——agent 会自己找路，跑通后把路书写回来。

然后换 bug 模式跑同一个场景：

```
http://localhost:4173/?bug=optimistic
```

这个模式下新任务会渲染、header 计数器也会变，但**从不写入存储**。加完的那一刻一切正常。
裁判照样抓得到，因为那两屏都是它自己加载出来的、不是 runner 留下的——你会拿到
`FAIL`，证据是引用的页面原文「还没有任务。」。

一条命令就能复现这套设计的全部理由。真跑出来的一套产物原样放在
[`docs/example-run/`](docs/example-run/)，可以先看那个再决定要不要装。

## 换一个真实产品：Gitea

`demo-app/` 够用来说清纪律，但证明不了「换一个陌生界面还成不成立」——它是个单 HTML 文件、
没有后端，状态只活在 localStorage 里。所以仓库里还有第二条路：一个**真实的开源产品**。

```bash
targets/gitea/launch.sh          # 本地起一个 Gitea 实例（:3100，单文件二进制 + SQLite）
/roadbook gitea-issue-flow       # 注册 → 建仓库 → 开工单 → 评论 → 关闭
```

选 Gitea 是因为它三样都占：单文件二进制不用 Docker、界面服务端渲染正文读得到、
主流程每一步都真的写库——正好对上这套东西的立身之本。取舍和清理方式写在
[`targets/gitea/README.md`](targets/gitea/README.md)（清理是 `scripts/cleanup_gitea_user.sh <用户名>`）。

这条场景是**首跑探索就 PASS** 的：runner 从 0 步勘出五步路书，裁判自己重新加载工单详情页
和列表页，抄到的页面原文是「已关闭」、评论正文、以及列表页的「0 开启中 / 1 已关闭」。
之后两次回放（照写好的路书走）同样 PASS。产物在 `runs/20260930-114022-gitea-issue-flow/`
（探索那次）和 `runs/20260930-120550-gitea-issue-flow/`（最后一次回放）。

## 换一个不需要起服务的靶子：公网只读

上面两个靶子都要么本地起服务、要么自己造数据。还有两条**什么都不用准备**的场景，被测的是
公网上现成的大站，全程只读、不登录：

| 场景 | 靶子 | 验什么 |
|---|---|---|
| `github-repo-flow` | GitHub 上的 react/react | 仓库页、工单列表、工单详情三屏都加载出对得上的内容 |
| `gov-policy-doc` | 中国政府网 · 政策频道 | 从「最新政策」挑最新一条国务院文件，核对标题、发文机关、发文字号、成文日期、索引号和归档面包屑 |

```bash
/roadbook github-repo-flow       # 3 步 8 条
/roadbook gov-policy-doc         # 3 步 10 条
```

`gov-policy-doc` 是三条公网场景里**最难**的一条：详情页那份官方文件的元数据表要逐项读
（索引号、发文机关、发文字号、成文日期、发布日期），还要求它们之间自洽——发文机关要对上
标题主体、成文日期不能晚于发布日期、面包屑要把文件归在「信息公开 > 国务院文件」下。
它证明了这套东西不止能点几个链接，还能读一张字段表并做跨字段的一致性判断。

两条都实测 PASS。产物在 `runs/20260930-141820-github-repo-flow/` 和
`runs/20260930-151453-gov-policy-doc/`——注意 `runs/` 跟其它 run 一样**不进 git**
（里面有你那台机器跑出来的真实值），自己跑一次就会有。

顺带说清这两条场景里 `context.*` 是怎么处理的，因为它常被写错：**只有「跑的时候才知道」
的值才用变量**（比如「点开的是哪一条工单」）。写死的地址——`https://www.gov.cn/zhengce/`
这种——直接写进验收路线，不要为它造一个变量。哪些变量存在、它们上次取的什么值，
看板「怎么算过」页签里都列着，点一下就插进正文。

## 接到你自己的产品

先建一个**项目**文件夹（一个被测对象一个，一对多场景），再往里放场景。一个场景 = 一个目录，
里面三份文件，人写两份、agent 写一份：

```
scenarios/<项目名>/           ← 项目 = 被测对象，比如你的产品名
  <场景名>/
    intent.md      【你写】开头一段 frontmatter（name、一句话 description），正文是目标、固定参数、红线、造数、清理——不写步骤
    expect.yaml    【你写】裁判的验收路线：按顺序去哪、看什么
    playbook.md    【agent 写】首跑探索后自动生成，之后每次回放它、失配时更新它
```

只有一两个场景时懒得建项目层？旧式平铺 `scenarios/<场景名>/` 仍然合法，两种可以混用。

1. 建目录，写 `intent.md` 和 `expect.yaml`。`python3 tests/test_examples.py` 会告诉你格式对不对，
   比如 check 写成了「创建成功」这种主题词而不是页面上能读到的事实。
2. `/roadbook <场景名>` 跑第一次。没有路书，agent 进探索模式自己找路，跑通后把 `playbook.md` 写回来。
   把它连同 `intent.md`、`expect.yaml` 一起提交。
3. 之后每次都是回放。路书失配时 agent 从出问题的那步重新勘路、改路书，**路书的 diff 就是界面的变更记录**。

同一条路要用不同的值跑（时长 5 天还是 10 天）？多建一个场景目录，各写各的 `expect.yaml`。
路书是一条录音，录音里不该有 if。

场景多了之后怎么挑：`python3 scripts/scenarios.py` 一行一个场景（名字 + 一句话说它验什么），
`python3 scripts/scenarios.py <候选>` 只看候选的「什么时候跑」。SKILL.md 里写了让 agent 按这个顺序挑，
不要一上来把所有 intent.md 都读进上下文。

## 一次 run 留下什么

```
runs/20260909-1057-todo-persistence/
  verdict.txt        PASS — 2 步 4 条 check 全部通过，均附页面原文证据
  judge-output.txt   记分器的逐条输出，结论的唯一依据
  context.yaml       runner 留的基线（id、它实际输入的名称、操作前的值）
  judgment.yaml      裁判的逐条回答，每条带页面原文
  runner-notes.md    runner 的过程记录，不是判据
```

`runs/` 不进 git——里面有你那个环境的真实 id、账号名、余额。

`atoms/` 是 agent **自己沉淀**的被测产品操作记忆——每个节点长什么样、有哪些变体、
踩过什么坑，跑一次长一点，人不预先写。首跑时它是空的，正常。回放顺利时 agent 不会翻它；
遇到不确定的操作、或某一步失配了，先 `python3 scripts/atoms.py` 查索引再自己试。
路书每步的 `【参考】` 指向对应原子，由 agent 沉淀时回填。原子"验过没有"不靠人填，
`scripts/atoms_status.py` 从 PASS 的 run 推导出来写进 `atoms/STATUS.md`。
这一层的设计参考了 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的 skills / memory 机制：
教训不是日志、只警告不拦的 linter、只归档不删的生命周期。

## 诚实的短板

- **无人值守能跑了，但还没在真正的 CI 里跑过。** `claude -p "/roadbook <场景>"` 配
  Playwright MCP 已经实测跑通一条真实产品的登录场景（识别运行时 → 回放 → 留事实），
  形状和坑记在 [`docs/porting.md`](docs/porting.md) 的 Headless / CI 段。
  但那是在一台开发机上以无头方式跑的，**还没有在 GitHub Actions 这类托管 runner 上验证过**——
  网络、浏览器依赖、并发都可能再冒出问题。
- **证据基础很薄。** 一个真实产品、两个场景、六次 run、大约一周；加上本仓库四个演示场景各跑过一次 PASS。
  [`references/browser-pitfalls.md`](references/browser-pitfalls.md) 里的坑全是实测的；
  但框架的普适性还没被证明。
- **真花 token。** 五步流程实测：裁判一次约 70–90k tokens、3–7 分钟。把 `expect.yaml`
  从"一堆无序声明"改成**有序路线**之后，裁判的工具调用从 24 次降到 10 次——因为它不用
  自己规划找路了。按这个量级预算，这不是每次提交都能跑的检查。
- **工具耦合已经拆开，但只验过两套。** 资产层（场景、路书、原子）现在只说能力名，
  工具名集中在 [`references/runtimes/`](references/runtimes/) 下、一个运行时一个文件，
  `tests/lint_atoms.py` 机械拦住往资产里写工具名（禁用词从运行时文件自动提取）。
  加第三套运行时应该只是加一个文件，但**这个"应该"还没被第三套验证过**。
- **它只回答一个问题。** "这条流程还跑得通吗"，不回答"为什么坏"。日志和数据库取证是
  刻意排除在外的。
- **渐进式披露是纪律不是机制。** 场景和原子的索引靠 SKILL.md 里的规矩和两个脚本，
  harness 不知道它们的存在；agent 不照做的话没有东西拦它。

## 与其它工具的关系

不是 [Midscene](https://github.com/web-infra-dev/midscene)、
[Browser Use](https://github.com/browser-use/browser-use) 或 Playwright 的替代品，
而是可以叠在它们之上的一层纪律。Midscene 解决的是确定、廉价的回放（它的 plan cache
和路书是同一个直觉），并提供一个返回布尔值的自然语言断言。路书的贡献是那之后的部分：
**谁有资格下判决，判决必须由什么兜底**。如果你已经在用 `aiQuery` 取值、再用自己的代码
比对，那你已经同意这个仓库一半的主张了。

## 目录

```
SKILL.md                          驾驶纪律：两种模式、标准流程、硬边界、怎么挑场景、什么时候查原子
references/
  judge-protocol.md               原样交给裁判 agent
  verdict-rules.md                谁判、PASS/FAIL/BLOCK、共享账号规矩
  exploration-rules.md            路书格式与更新纪律
  browser-pitfalls.md             跟运行时无关的坑；先读这个
  runtime-contract.md             能力词表 + 资产层不写工具名这条纪律
  runtimes/
    claude-pane.md                Claude Code 桌面版浏览器 pane 的绑定与专属坑
    playwright-mcp.md             无头容器里的绑定与专属坑
scripts/
  judge.py                        唯一产出结论的代码：判决 → 退出码
  scenarios.py                    列场景供挑选
  atoms.py                        列原子供回忆
  atoms_status.py                 从 PASS run 推导原子状态，生成 atoms/STATUS.md
scenarios/                        自带的场景，按被测对象分项目，一对多
  demo-app/                         演示应用（上面 demo-app/ 那个）的项目
    todo-persistence/                 加一条，刷新后还在
    todo-batch-add/                   连加三条——和上面是两个场景，不是一个场景带参数
    todo-complete/                    勾一条已完成，状态是存下来的
    todo-reset/                       重置按钮真清了存储，不只是画空
  gitea/gitea-issue-flow/           开源产品主流程：注册 → 建仓库 → 开工单 → 评论 → 关闭
  github/github-repo-flow/          公网只读：GitHub 仓库 → 工单列表 → 工单详情
  gov-site/gov-policy-doc/          公网只读：中国政府网政策文件，读一整套官方元数据
atoms/                            agent 沉淀的被测产品记忆；README 是规矩，STATUS 是账本
config/
  env.json                        环境说明：demo 靶子的地址（只有 localhost，没有密钥）；
                                  场景里 `environments.<env>.xxx` 这类引用指的就是它
demo-app/                         被测的演示应用，bug 可开关
targets/gitea/                    另一个靶子：真实的开源产品，launch.sh 起、cleanup.sh 清
tests/                            四项检查：记分器、场景、路书、原子
docs/
  example-run/                    一次真实 run 的全部产物
  porting.md                      换别的浏览器工具怎么接
```

## 状态

`v0.1.0`，从一套内部 QA 方案里抽出来，仓库从一个全新提交开始。内核可用；CI 方案和移植说明还没定。
现在最有价值的贡献是**来自其它产品的场景**——这套设计需要接触它没被开发过的界面。
怎么交见 [CONTRIBUTING.md](CONTRIBUTING.md)。

MIT 许可，见 [LICENSE](LICENSE)。English summary: [README.en.md](README.en.md)。
