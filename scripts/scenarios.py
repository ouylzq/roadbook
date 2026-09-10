#!/usr/bin/env python3
"""列场景，供挑选。渐进式披露的第 1、2 层各一个命令，第 3 层才是读整份 intent.md。

    python3 scripts/scenarios.py                 # 第 1 层：每个场景一行——name  description
    python3 scripts/scenarios.py <场景名>...      # 第 2 层：只打印这几个候选的「## 什么时候跑」
    python3 scripts/scenarios.py --root <目录>    # scenarios/ 在别的项目下时

读的是每个 scenarios/<名>/intent.md 开头的 YAML frontmatter（name / description），
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
    dirs = sorted(p for p in scen_dir.iterdir() if p.is_dir() and (p / "intent.md").exists()) if scen_dir.exists() else []
    if not dirs:
        print(f"{scen_dir} 下没有场景")
        return 1

    if not args:                                       # 第 1 层
        width = max(len(d.name) for d in dirs)
        for d in dirs:
            fm, _ = frontmatter(d / "intent.md")
            desc = str(fm.get("description") or "").strip() or "（intent.md 缺 frontmatter/description，lint 应已拦住）"
            print(f"{d.name.ljust(width)}  {desc}")
        return 0

    rc = 0                                             # 第 2 层
    for name in args:
        d = scen_dir / name
        if not (d / "intent.md").exists():
            print(f"{name}: 没有这个场景（有的是：{', '.join(x.name for x in dirs)}）")
            rc = 1
            continue
        fm, body = frontmatter(d / "intent.md")
        m = WHEN_RE.search(body)
        when = m.group(1).strip() if m else "（正文缺「## 什么时候跑」，lint 应已拦住）"
        print(f"## {name} —— {str(fm.get('description') or '').strip()}\n{when}\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
