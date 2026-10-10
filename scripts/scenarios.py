#!/usr/bin/env python3
"""列场景，供挑选。渐进式披露的第 1、2 层各一个命令，第 3 层才是读整份 intent.md。

    python3 scripts/scenarios.py                 # 第 1 层：每个场景一行——name  project  description
    python3 scripts/scenarios.py <场景名>...      # 第 2 层：只打印这几个候选的「## 什么时候跑」
    python3 scripts/scenarios.py --root <目录>    # scenarios/ 在别的项目下时

目录布局两认：`scenarios/<项目>/<场景>/`（项目 = 被测对象，一对多场景）和旧式的
一层平铺 `scenarios/<场景>/`，混用也行。场景的身份始终是目录名，全仓库不许重名——
项目只是分组，不是命名空间。

读的是每个 intent.md 开头的 YAML frontmatter（name / description），
按 YAML 解析，不押文件长相；frontmatter 缺失或坏了会在那一行明说，而不是静默漏掉。
"""
import re
import sys
from pathlib import Path

import yaml

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
WHEN_RE = re.compile(r"^## 什么时候跑\s*\n(.*?)(?=^## |\Z)", re.S | re.M)


def frontmatter(intent: Path) -> tuple[dict, str]:
    text = intent.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return {}, text
    try:
        return (yaml.safe_load(m.group(1)) or {}), text[m.end():]
    except yaml.YAMLError:
        return {}, text


def discover(scen_dir: Path) -> list[tuple[str | None, Path]]:
    """[(项目名或None, 场景目录)]。带 intent.md 的是场景；不带而子目录带的，是项目。"""
    out: list[tuple[str | None, Path]] = []
    if not scen_dir.exists():
        return out
    for child in sorted(scen_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / "intent.md").exists():               # 旧式平铺：scenarios/<场景>/
            out.append((None, child))
            continue
        out.extend((child.name, d) for d in sorted(child.iterdir())
                   if d.is_dir() and not d.name.startswith(".")
                   and (d / "intent.md").exists())
    return out


def main() -> int:
    args = sys.argv[1:]
    root = Path.cwd()
    if "--root" in args:
        i = args.index("--root")
        root = Path(args[i + 1]).resolve()
        del args[i:i + 2]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    scen_dir = root / "scenarios"
    found = discover(scen_dir)
    if not found:
        print(f"{scen_dir} 下没有场景")
        return 1

    if not args:                                       # 第 1 层
        width = max(len(d.name) for _, d in found)
        pwidth = max(len(p or "—") for p, _ in found)
        for project, d in found:
            fm, _ = frontmatter(d / "intent.md")
            desc = str(fm.get("description") or "").strip() or "（intent.md 缺 frontmatter/description，lint 应已拦住）"
            print(f"{d.name.ljust(width)}  {(project or '—').ljust(pwidth)}  {desc}")
        return 0

    rc = 0                                             # 第 2 层
    for name in args:
        hits = [(p, d) for p, d in found if d.name == name or f"{p}/{d.name}" == name]
        if not hits:
            print(f"{name}: 没有这个场景（有的是：{', '.join(d.name for _, d in found)}）")
            rc = 1
            continue
        if len(hits) > 1:
            full = ", ".join(f"{p}/{d.name}" for p, d in hits)
            print(f"{name}: 场景名重名了（{full}）——场景目录名必须全仓库唯一，用 项目/场景名 消歧")
            rc = 1
            continue
        project, d = hits[0]
        fm, body = frontmatter(d / "intent.md")
        m = WHEN_RE.search(body)
        when = m.group(1).strip() if m else "（正文缺「## 什么时候跑」，lint 应已拦住）"
        print(f"## {d.name} —— {str(fm.get('description') or '').strip()}\n{when}\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
