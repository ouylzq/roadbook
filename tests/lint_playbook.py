#!/usr/bin/env python3
"""检查每份 playbook.md 的每一步都合规。

    python3 tests/lint_playbook.py

每步必须：
  - 有【参考】，值是 atoms/ 里存在的文件名，或 —
  - 四要素齐全：【目的】【锚点】【动作】【到位标志】

格式见 references/exploration-rules.md。这是把"写不出到位标志就是没勘明白"和
"每步都得说清失配时翻哪本手册"从纪律变成校验。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATOMS = {p.stem for p in (ROOT / "atoms").glob("*.md")} - {"README", "STATUS"}
PLAYBOOKS = sorted((ROOT / "scenarios").glob("*/playbook.md"))

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


def lint(path: Path) -> list[str]:
    errs: list[str] = []
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    if "最后勘路" not in text:
        errs.append(f"{rel}: 文件头缺「最后勘路：<日期>」")
    steps = steps_of(text)
    if not steps:
        errs.append(f"{rel}: 没找到任何步骤（「## 步骤」下要有 `1. ` 开头的条目）")
        return errs
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
        print("scenarios/ 下没有 playbook.md（首跑探索后才会生成），跳过")
        return 0
    all_errs: list[str] = []
    for pb in PLAYBOOKS:
        errs = lint(pb)
        print(f"  {'ok  ' if not errs else '失败'} {pb.relative_to(ROOT)}  ({len(steps_of(pb.read_text(encoding='utf-8')))} 步)")
        all_errs += errs
    for e in all_errs:
        print(f"       {e}")
    print(f"\n{len(PLAYBOOKS) - len({e.split(':')[0] for e in all_errs})}/{len(PLAYBOOKS)} 份路书合规")
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
