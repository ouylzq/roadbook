#!/usr/bin/env python3
"""从 run 记录推导每个原子的验证状态，生成 atoms/STATUS.md。

    python3 scripts/atoms_status.py            # 以仓库根为基准
    python3 scripts/atoms_status.py <根目录>    # scenarios/、runs/、atoms/ 都在这个目录下

规则（见 atoms/README.md「状态由 run 推导，不许手写」）：
  已验证        某个 PASS run 的路书【参考】了它，且最近一次在 30 天内
  陈旧          上次被 PASS run 经过是 30～90 天前——界面可能变了，回放到它时多留意
  归档候选      超过 90 天没被任何 PASS run 经过。只归档不删：挪进 atoms/.archive/，要用再挪回
  已引用，未验证  有路书引用它，但没有任何 PASS run 经过
  待勘          没有任何路书引用它（存根原子——看到了没走的分支——就是这个状态）

生命周期照 Hermes 的 curator：从最近一次真实活动推导状态，永不删除，只归档。

「description」列取自每个原子文件开头 frontmatter 的 description，和 scripts/atoms.py 列出来的是同一句。

run 目录名约定 <YYYYMMDD-HHmm>-<场景名>，场景名用来找到对应的 playbook.md。
runs/ 通常被 gitignore，所以 STATUS.md 反映的是**生成它的那台机器**跑过的东西——
提交它的人就是在为这份账本背书。
"""
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

STALE_AFTER_DAYS, ARCHIVE_AFTER_DAYS = 30, 90

RUN_DIR_RE = re.compile(r"^(\d{8})-\d{4}-(.+)$")
REF_RE = re.compile(r"【参考】\s*([A-Za-z0-9_\-]+|—)")


def describe(root: Path, name: str) -> str:
    """原子 frontmatter 里的 description。"""
    text = (root / "atoms" / f"{name}.md").read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "（缺 frontmatter，lint 应已拦住）"
    try:
        return str((yaml.safe_load(m.group(1)) or {}).get("description") or "").strip() or "（缺 description）"
    except yaml.YAMLError:
        return "（frontmatter 不是合法 YAML）"


def atom_names(root: Path) -> list[str]:
    return sorted(
        p.stem for p in (root / "atoms").glob("*.md")
        if p.stem not in ("README", "STATUS")
    )


def playbook_refs(root: Path) -> dict[str, list[str]]:
    """场景名 → 该路书引用的原子名列表（去掉 —）。"""
    refs: dict[str, list[str]] = {}
    # 布局两认：scenarios/<项目>/<场景>/ 和旧式平铺 scenarios/<场景>/，混用也行。
    playbooks = sorted(
        set((root / "scenarios").glob("*/playbook.md"))
        | set((root / "scenarios").glob("*/*/playbook.md"))
    )
    for pb in playbooks:
        names = [m for m in REF_RE.findall(pb.read_text(encoding="utf-8")) if m != "—"]
        refs[pb.parent.name] = names
    return refs


def pass_runs(root: Path) -> list[tuple[str, str]]:
    """[(日期, 场景名)]，只收 verdict 以 PASS 开头的 run。"""
    out = []
    runs = root / "runs"
    if not runs.exists():
        return out
    for d in sorted(runs.iterdir()):
        m = RUN_DIR_RE.match(d.name)
        v = d / "verdict.txt"
        if not (m and v.exists()):
            continue
        if v.read_text(encoding="utf-8").lstrip().startswith("PASS"):
            out.append((m.group(1), m.group(2)))
    return out


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    atoms = atom_names(root)
    refs = playbook_refs(root)
    passes = pass_runs(root)

    referenced_by: dict[str, set[str]] = defaultdict(set)     # 原子 → 场景
    for scenario, names in refs.items():
        for n in names:
            referenced_by[n].add(scenario)

    verified: dict[str, tuple[str, str]] = {}                  # 原子 → (最近日期, 场景)
    for run_date, scenario in passes:
        for n in refs.get(scenario, []):
            if n not in verified or run_date > verified[n][0]:
                verified[n] = (run_date, scenario)

    dangling = sorted(n for n in referenced_by if n not in atoms)

    lines = [
        "# 原子状态账本",
        "",
        "> 由 `scripts/atoms_status.py` 生成，**别手改**。状态只来自 PASS 的 run，不是谁觉得它验过了。",
        f"> 生命周期：{STALE_AFTER_DAYS} 天没被 PASS run 经过记陈旧，{ARCHIVE_AFTER_DAYS} 天记归档候选；只归档不删。",
        f"> 依据：{len(passes)} 个 PASS run，{len(refs)} 份路书，{len(atoms)} 个原子。",
        "",
        "| 原子 | description | 状态 | 最近验证 | 被哪些路书引用 |",
        "|---|---|---|---|---|",
    ]
    counts = defaultdict(int)
    today = date.today()
    for n in atoms:
        if n in verified:
            d, scenario = verified[n]
            age = (today - date(int(d[:4]), int(d[4:6]), int(d[6:]))).days
            status = "已验证" if age < STALE_AFTER_DAYS else ("陈旧" if age < ARCHIVE_AFTER_DAYS else "归档候选")
            when = f"{d[:4]}-{d[4:6]}-{d[6:]} · {scenario}（{age} 天前）"
        elif n in referenced_by:
            status, when = "已引用，未验证", "—"
        else:
            status, when = "待勘", "—"
        counts[status] += 1
        used = "、".join(sorted(referenced_by.get(n, []))) or "—"
        lines.append(f"| `{n}` | {describe(root, n)} | {status} | {when} | {used} |")

    lines += ["", "汇总：" + "，".join(f"{k} {v}" for k, v in counts.items()) + "。"]
    if dangling:
        lines += ["", "⚠️ 路书引用了不存在的原子（lint 应该已经拦住）：" + "、".join(f"`{n}`" for n in dangling)]

    out = root / "atoms" / "STATUS.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n写入 {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
