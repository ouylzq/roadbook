#!/usr/bin/env python3
"""列原子，供回忆。渐进式披露的第 1、2 层各一个命令，第 3 层才是读整个原子。

    python3 scripts/atoms.py                 # 第 1 层：每个原子一行——name + description 的第一段（节点是什么）
    python3 scripts/atoms.py --long          # 同上，但 description 整句
    python3 scripts/atoms.py --grep <词>      # 只列 description 或正文里含这个词的原子（锚点文案、报错文案都行）
    python3 scripts/atoms.py <原子名>...      # 第 2 层：只打印这几个候选的「## 它长什么样」
    python3 scripts/atoms.py --root <目录>    # atoms/ 在别的项目下时

第 1 层默认只打 description 的第一段——冒号之前那几个字，说的是"哪个应用的哪个节点"。
原子多起来（几十上百个）时每次失配扫一遍全量整句会吃掉几千 token，而决定"要不要打开它"
通常看节点名就够；看不够再 --long 或 --grep 缩小范围。

读的是每个 atoms/<名>.md 开头的 YAML frontmatter（name / description），不押文件长相。
"""
import re
import sys
from pathlib import Path

import yaml

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LOOK_RE = re.compile(r"^## 它长什么样\s*\n(.*?)(?=^## |\Z)", re.S | re.M)
SKIP = {"README", "STATUS"}


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return {}, text
    try:
        return (yaml.safe_load(m.group(1)) or {}), text[m.end():]
    except yaml.YAMLError:
        return {}, text


def head_clause(desc: str) -> str:
    """description 的第一段：到第一个冒号为止；没有冒号就到第一个句号。"""
    for sep in ("：", ":"):
        if sep in desc:
            return desc.split(sep, 1)[0]
    return desc.split("。", 1)[0]


def main() -> int:
    args = sys.argv[1:]
    root = Path.cwd()
    if "--root" in args:
        i = args.index("--root")
        root = Path(args[i + 1]).resolve()
        del args[i:i + 2]
    long = "--long" in args
    if long:
        args.remove("--long")
    grep = None
    if "--grep" in args:
        i = args.index("--grep")
        grep = args[i + 1]
        del args[i:i + 2]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    atoms_dir = root / "atoms"
    files = sorted(p for p in atoms_dir.glob("*.md") if p.stem not in SKIP) if atoms_dir.exists() else []
    if not files:
        print(f"{atoms_dir} 下还没有原子——首跑时这是正常的")
        return 0

    if not args:                                       # 第 1 层
        rows = []
        for p in files:
            fm, body = frontmatter(p)
            d = str(fm.get("description") or "").strip()
            if grep and grep not in d and grep not in body:
                continue
            shown = (d if long else head_clause(d)) if d else "（缺 frontmatter/description，lint 应已拦住）"
            rows.append((p.stem, shown))
        if not rows:
            print(f"没有原子的 description 或正文含「{grep}」")
            return 0
        width = max(len(n) for n, _ in rows)
        for n, shown in rows:
            print(f"{n.ljust(width)}  {shown}")
        if not long and not grep:
            print(f"\n（{len(rows)} 个原子；整句用 --long，按文案筛用 --grep <词>）")
        return 0

    rc = 0                                             # 第 2 层
    for name in args:
        p = atoms_dir / f"{name}.md"
        if not p.exists():
            print(f"{name}: 没有这个原子（有的是：{', '.join(f.stem for f in files)}）")
            rc = 1
            continue
        fm, body = frontmatter(p)
        m = LOOK_RE.search(body)
        look = m.group(1).strip() if m else "（缺「## 它长什么样」，lint 应已拦住）"
        print(f"## {name} —— {str(fm.get('description') or '').strip()}\n{look}\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
