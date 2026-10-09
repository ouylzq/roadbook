# 运行时：Playwright MCP

无头容器 / CI 里跑时用的运行时。没有人在旁边看，所以**一切靠文本取证，截图只是留档**。

用的是微软官方的 [`@playwright/mcp`](https://github.com/microsoft/playwright-mcp)。

## 怎么认出是我

工具里有 `browser_snapshot`、`browser_take_screenshot`、`browser_navigate` 这一组
（`mcp__playwright__browser_*`）。

## 能力绑定

| 能力 | 工具 |
|---|---|
| 看画面 | `browser_take_screenshot` |
| 按坐标点 | `browser_mouse_click_xy`（**要启 `--caps=vision`**，否则没有这个工具） |
| 读页面文本 | `browser_snapshot`（可访问树带文字），或用只读脚本取 innerText |
| 读页面结构 | `browser_snapshot`（产出元素引用） |
| 按引用点 | `browser_click`，带元素引用 |
| 找元素 | `browser_find` |
| 打字 | `browser_type`（`browser_fill_form` 批量填） |
| 写表单值 | `browser_evaluate` 里赋值，或 `browser_fill_form` |
| 打开网址 | `browser_navigate` |
| 跑只读脚本 | `browser_evaluate` |
| 设视口 | `browser_resize`（也可用启动参数 `--viewport-size`） |
| 管标签页 | `browser_tabs` |
| 提议原子 | 看编排它的运行时给不给记忆层。没给就跟桌面一样：直接编辑 atoms/<节点>.md 文件，守 atoms/README.md「谁能写」的规则 |
| 给候选投票 | 同上；没有记忆层就没有候选可投 |

另有桌面 pane 没有的：`browser_file_upload`（真的能上传文件）、`browser_wait_for`、
`browser_console_messages`、`browser_network_requests`、`browser_storage_state`。

## 启动参数（由跑它的地方配，不是路书的事）

```
npx @playwright/mcp@latest --headless --isolated --caps=vision --viewport-size 1280x900
```

- `--headless` 无头。CI 里没有显示器，必须带。
- **`--user-data-dir <目录>` 让 runner 和裁判共用一份登录态。** 裁判是另起的进程、另开的浏览器，
  用 `--isolated`（profile 跑完即焚）的话它会是未登录态，而协议要求它自己加载每一屏。
  两个进程是先后跑的，不会争同一份 profile。**并发跑多个场景时给每个场景各一个目录。**
- `--caps=vision` 才有按坐标点的能力。不带就只能按引用点。
- `--storage-state <file>` 可以把登录态灌进来，跳过登录步骤。**默认不用**——
  登录本身也是要回归的一条路，跳过它等于少测一段。

## 这个运行时特有的坑

### 没有人能接管

桌面版卡住了人可以伸手点一下，这里不行。所以：

- **任何"等人处理"的分支都是 BLOCK，不是等待。** 撞上人机验证、需要手机验证码、
  需要人点确认的地方，直接写 `blocked.txt` 停下。
- 超时要设死。步骤级别卡住不动，宁可判 BLOCK 也不要挂在那里烧钱。

### 截图是留档，不是判据（这里比桌面版更绝对）

桌面版至少有人能瞥一眼截图。这里没人看，截图只在事后翻 run 目录时才有用。
**所有判断都必须从页面文本或只读脚本的返回值里来**，一条都不许例外。

### 按引用点比按坐标点可靠

`browser_snapshot` 产出的 ref 是 Playwright 自己的元素句柄，不受滚动和动画影响；
按坐标点则和桌面版一样会踩动画中间帧的坑。

**所以这个运行时的默认驱动方式和桌面版相反：优先按引用点，坐标是退守。**
资产层不用管这个区别——路书里写「点发送键」，用哪种方式由这里决定。

### 读页面文本要窄，别整棵树都要

`browser_snapshot` 给的是整页可访问树。真实产品的列表页能吐出几万 token，
连着几屏就把上下文顶满——实测触发过 autocompact 反复抖动、整个 run 失败。

**取证时优先用只读脚本取你要的那一段**（例如主内容区的 `innerText`、某个区域的文字），
整棵 snapshot 留给"我需要一个能点的引用"那种时候。要引用原文作证据时，
引窄一点：一句话、一个数字，不要整屏粘贴。

### 裁判是外部编排的独立进程，不是 subagent

无头模式下 runner 手上不一定有起 subagent 的工具（`--bare` 就没有）。
这个运行时里：

- **runner 走到"留下事实"为止**——把 `context.yaml` 写好就停，不自己起裁判、更不自己判。
- **裁判由外面再起一个进程**，上下文干净，只交给它三样：`references/judge-protocol.md` 全文、
  场景的 `expect.yaml`、本次的 `context.yaml`，外加被测环境的域名。
- 它产出 `judgment.yaml` 之后，外面跑 `scripts/judge.py <场景目录> <run目录>` 换算退出码。

分离比 subagent 更彻底（两个进程，各自干净），代价是编排要写在外面。

### 无头模式下有些东西表现不一样

没有真实窗口，所以：动画可能跑得更快或直接跳过；`window.open` 行为可能不同；
某些只在 hover 时出现的元素要显式 hover 才拿得到。遇到和桌面版不一致的，
**先怀疑是无头差异，不要当成产品 bug 上报**。
