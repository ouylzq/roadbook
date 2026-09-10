# 一次真实 run 留下的东西

这是 2026-09-09 在本仓库的演示场景上真跑出来的一套产物，原样拷过来（`runs/` 本身被 gitignore）。
runner 按 `scenarios/todo-persistence/playbook.md` 回放四步，裁判是独立 agent，
`judge.py` 给出退出码 0。

| 文件 | 谁写的 | 看什么 |
|---|---|---|
| `context.yaml` | runner | 留给裁判的基线——这次只有它实际输入的标题 |
| `judgment.yaml` | 裁判 | 每条 check 的 result + how + evidence 原文 |
| `judge-output.txt` | judge.py | 逐条记分，结论的唯一依据 |
| `verdict.txt` | judge.py | 一行结论 |
| `runner-notes.md` | runner | 过程记录，不是判据 |

值得留意 `judgment.yaml` 里 header 计数器那条：`get_page_text` 读不到 `<main>` 之外的东西，
裁判按协议退守 `read_page`，并在 `how` 里写明了原因——这就是"退守要留痕"的样子。
期望的数字都写在 `expect.yaml` 里，`context.yaml` 只有 runner 实际输入的标题——期望值不由 runner 转述。
