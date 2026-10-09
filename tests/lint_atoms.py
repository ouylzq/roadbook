#!/usr/bin/env python3
"""原子文件的检查。格式错是错误，写法差只警告——照 Hermes 的 advisory linter：警告不拦写入，
但每次都会看见。

    python3 tests/lint_atoms.py

错误（退出码 1）：
  - 开头缺 frontmatter（name / description），或 name 和文件名不一致，或 description 不是一句完整的话（25～90 字）
  - 缺「## 它长什么样」
  - 出现了运行时的具体工具名——资产层只许用能力词表，见 references/runtime-contract.md。
    禁用词不是写死的：从 references/runtimes/*.md 的「能力绑定」表里自动提取，
    所以**新加一个运行时，这项检查自动覆盖它的工具名**，不用改这个脚本。
  - 正文里出现了来源 / 票的标记（跑批 id、候选 id、HTML 注释）——来源和票记在运行时的账本里，
    正文只写教训，见 atoms/README.md「谁能写」

警告（只打印）：
  - 写成了日志：出现日期、或"本轮/今天/刚才/那次/上次/我把/我点"这类叙事词 ≥ 3 处
    ——规则必须脱离故事也成立，日期交给 git log
  - 「已知会失败的方式」里的条目没有「→」——要写成 现象 → 机制 → 对策
  - 超过 60 行——要么在写故事，要么该拆
  - 出现「第一步/步骤 1/1.」式的流程叙述——流程是路书的活

规矩全文见 atoms/README.md。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ATOMS = sorted(p for p in (ROOT / "atoms").glob("*.md") if p.stem not in ("README", "STATUS"))

RUNTIMES = ROOT / "references" / "runtimes"

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
NARRATION = ("本轮", "今天", "刚才", "那次", "上次", "我把", "我点", "我在", "当时", "结果报")
PROCEDURE_RE = re.compile(r"(第[一二三四五六七八九十\d]+步|^\s*\d+\.\s)", re.M)
# 来源和票不进正文：跑批 id（20260924-1030-login 这种）、候选 id（8 位十六进制）、HTML 注释
PROVENANCE_RE = re.compile(r"<!--|\brun_id\b|\b20\d{6}-\d{4,6}-[a-z][a-z0-9-]*\b|候选\s*[0-9a-f]{6,}|\[[0-9a-f]{8}\]")
MIN_DESC, MAX_DESC, MAX_LINES, MAX_NARRATION_HITS = 25, 90, 65, 3


def cjk_len(s: str) -> int:
    return len(s.replace(" ", ""))


def runtime_tool_names() -> dict[str, str]:
    """从各运行时文件的「能力绑定」表里抽出工具名 → 它属于哪个运行时。

    不写死任何名字：加一份 references/runtimes/<新的>.md，这里自动认出它的工具。
    只认表格行（以 | 开头）里反引号包着的标识符，所以正文里提到工具名不受影响。
    """
    names: dict[str, str] = {}
    for rt in sorted(RUNTIMES.glob("*.md")):
        body = rt.read_text(encoding="utf-8")
        m = re.search(r"^## 能力绑定\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
        if not m:
            continue
        for line in m.group(1).splitlines():
            if not line.lstrip().startswith("|"):
                continue
            for tok in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", line):
                names.setdefault(tok, rt.stem)
    return names


TOOL_NAMES = runtime_tool_names()


def section(body: str, title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def check(path: Path) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    m = FM_RE.match(text)
    if not m:
        errs.append(f"{rel}: 开头缺 frontmatter（---\\nname: …\\ndescription: …\\n---），scripts/atoms.py 靠它建索引")
    else:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            fm = {}
            errs.append(f"{rel}: frontmatter 不是合法 YAML：{e}")
        if fm.get("name") != path.stem:
            errs.append(f"{rel}: frontmatter 的 name 应该等于文件名 {path.stem!r}，实际是 {fm.get('name')!r}")
        d = str(fm.get("description") or "").strip()
        n = cjk_len(d)
        if n < MIN_DESC:
            errs.append(f"{rel}: description 只有 {n} 字，像个动作片段——要说清哪个应用的哪个节点、长什么样、什么时候来查它")
        elif n > MAX_DESC:
            errs.append(f"{rel}: description {n} 字，超过 {MAX_DESC}——一句话说清节点、样子、何时查就够，细节放正文")

    if not section(text, "它长什么样").strip():
        errs.append(f"{rel}: 缺「## 它长什么样」（失败者要靠它确认自己站在对的地方）")

    for tok, rt in sorted(TOOL_NAMES.items()):
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", text):
            errs.append(
                f"{rel}: 出现了运行时工具名 {tok!r}（属于 {rt}）——原子要换一套工具跑就废了。"
                f"改成 references/runtime-contract.md 的能力词；这个坑只在该运行时成立的话，"
                f"整条搬去 references/runtimes/{rt}.md"
            )

    if PROVENANCE_RE.search(text):
        errs.append(f"{rel}: 正文里出现了来源 / 票的标记（跑批 id、候选 id、HTML 注释）——"
                    f"来源和票记在运行时的账本里，正文只写教训（atoms/README.md「谁能写」）")

    hits = len(DATE_RE.findall(text)) + sum(text.count(w) for w in NARRATION)
    if hits >= MAX_NARRATION_HITS:
        warns.append(f"{rel}: 日期/叙事词出现 {hits} 处——像日志不像教训。写「现象 → 机制 → 对策」，日期交给 git log")

    fails = section(text, "已知会失败的方式")
    for ln in fails.splitlines():
        if ln.lstrip().startswith("- ") and "→" not in ln and not ln.lstrip().startswith("- …"):
            # 允许多行条目：只在该条目及其续行里都没有 → 时才警告
            warns.append(f"{rel}: 「已知会失败的方式」有条目没写成「现象 → 机制 → 对策」：{ln.strip()[:40]}…")
            break

    if len(lines) > MAX_LINES:
        warns.append(f"{rel}: {len(lines)} 行，超过 {MAX_LINES}——要么在写故事，要么这个节点该拆")

    body_wo_title = "\n".join(lines[1:])
    if PROCEDURE_RE.search(section(body_wo_title, "它长什么样")) or PROCEDURE_RE.search(section(body_wo_title, "变体")):
        warns.append(f"{rel}: 出现「第 N 步 / 1.」式流程叙述——流程是路书的活，原子只讲这个节点")

    return errs, warns


def main() -> int:
    if not ATOMS:
        print("atoms/ 为空（首跑前的正常状态），跳过")
        return 0
    all_errs, all_warns = [], []
    for p in ATOMS:
        e, w = check(p)
        all_errs += e
        all_warns += w
        print(f"  {'失败' if e else ('警告' if w else 'ok  ')} {p.relative_to(ROOT)}")
    for e in all_errs:
        print(f"       错误 {e}")
    for w in all_warns:
        print(f"       警告 {w}")
    bad = len({e.split(":")[0] for e in all_errs})
    print(f"\n{len(ATOMS) - bad}/{len(ATOMS)} 个原子格式合规，{len(all_warns)} 条写法警告")
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
