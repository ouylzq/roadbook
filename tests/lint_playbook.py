#!/usr/bin/env python3
"""检查每份 playbook.md 的每一步都合规。

    python3 tests/lint_playbook.py

每步必须：
  - 有【参考】，值是 atoms/ 里存在的文件名，或 —
  - 四要素齐全：【目的】【锚点】【动作】【到位标志】
  - 编号从 1 连续排下来，不断档、不重号

路书是**边勘边记**的：勘通一步记一步，失配就改写那一步。所以它随时可能只记到一半——
**半份路书是合法资产，不是半成品**，下次照着走到头再往前勘。但"只记到一半"和"根本没记"
是两回事：`playbook.md` 一旦存在就必须至少有一个完整的步骤，占位文本不算。
连续编号这条也是渐进式带来的——一步步追加和改写，编号断档是真会发生的事。

另有一条**警告**（不拦提交）：路书里出现运行时的具体工具名。路书是资产，
要能在不同运行时上回放，工具名会把它钉死在一套工具上。禁用词从
references/runtimes/*.md 自动提取，和 lint_atoms.py 同一份。原子上这是错误，
路书上先给警告——路书由 agent 维护，下次勘到那一步时会改写它。

格式见 references/exploration-rules.md。这是把"写不出到位标志就是没勘明白"和
"每步都得说清失配时翻哪本手册"从纪律变成校验。
"""
import re
import sys
from pathlib import Path

from lint_atoms import TOOL_NAMES

ROOT = Path(__file__).resolve().parent.parent
ATOMS = {p.stem for p in (ROOT / "atoms").glob("*.md")} - {"README", "STATUS"}
# 布局两认：scenarios/<项目>/<场景>/ 和旧式平铺 scenarios/<场景>/，混用也行。
PLAYBOOKS = sorted(
    set((ROOT / "scenarios").glob("*/playbook.md"))
    | set((ROOT / "scenarios").glob("*/*/playbook.md"))
)

STEP_RE = re.compile(r"^(\d+)\.\s", re.M)
REQUIRED = ("【目的】", "【锚点】", "【动作】", "【到位标志】")
REF_RE = re.compile(r"【参考】\s*([A-Za-z0-9_\-]+|—)")


def steps_of(text: str) -> list[tuple[str, str]]:
    """把「## 步骤」之后的正文切成 (编号, 该步全文)。"""
    body = text.split("## 步骤", 1)[1] if "## 步骤" in text else text
    body = body.split("\n## ", 1)[0]
    idx = [(m.start(), m.group(1)) for m in STEP_RE.finditer(body)]
    out = []
    for k, (start, num) in enumerate(idx):
        end = idx[k + 1][0] if k + 1 < len(idx) else len(body)
        out.append((num, body[start:end]))
    return out


def tool_name_warnings(rel: Path, text: str) -> list[str]:
    hits = sorted(
        tok for tok in TOOL_NAMES
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", text)
    )
    if not hits:
        return []
    return [f"{rel}: 出现运行时工具名 {', '.join(repr(h) for h in hits)}"
            f"——换个运行时回放就废了，改成 references/runtime-contract.md 的能力词"]


def lint(path: Path) -> list[str]:
    errs: list[str] = []
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    if "最后勘路" not in text:
        errs.append(f"{rel}: 文件头缺「最后勘路：<日期>」")
    steps = steps_of(text)
    if not steps:
        errs.append(f"{rel}: 没找到任何步骤（「## 步骤」下要有 `1. ` 开头的条目）"
                    "——路书可以只记到一半，但不能一步都没有；占位文本不是路书")
        return errs
    nums = [int(n) for n, _ in steps]
    if nums != list(range(1, len(nums) + 1)):
        errs.append(f"{rel}: 步骤编号应该是 1..{len(nums)} 连续排下来，实际是 {nums}"
                    "——边勘边记时追加或改写错了位置")
    for num, body in steps:
        m = REF_RE.search(body)
        if not m:
            errs.append(f"{rel}: 第 {num} 步缺【参考】（没有对应原子就写 —）")
        elif m.group(1) != "—" and m.group(1) not in ATOMS:
            errs.append(f"{rel}: 第 {num} 步引用了不存在的原子 {m.group(1)!r}（atoms/ 里有：{', '.join(sorted(ATOMS)) or '无'}）")
        for tag in REQUIRED:
            if tag not in body:
                errs.append(f"{rel}: 第 {num} 步缺{tag}")
    return errs


def main() -> int:
    if not PLAYBOOKS:
        print("scenarios/ 下没有 playbook.md（agent 勘通第一步时才会生成），跳过")
        return 0
    all_errs: list[str] = []
    all_warns: list[str] = []
    for pb in PLAYBOOKS:
        text = pb.read_text(encoding="utf-8")
        errs = lint(pb)
        warns = tool_name_warnings(pb.relative_to(ROOT), text)
        flag = "失败" if errs else ("警告" if warns else "ok  ")
        print(f"  {flag} {pb.relative_to(ROOT)}  ({len(steps_of(text))} 步)")
        all_errs += errs
        all_warns += warns
    for e in all_errs:
        print(f"       错误 {e}")
    for w in all_warns:
        print(f"       警告 {w}")
    print(f"\n{len(PLAYBOOKS) - len({e.split(':')[0] for e in all_errs})}/{len(PLAYBOOKS)} 份路书合规，{len(all_warns)} 条写法警告")
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
