#!/usr/bin/env python3
"""对每个场景的 expect.yaml 和 intent.md 做结构检查。

    python3 tests/test_examples.py

拦的是那些否则要等到花钱跑完浏览器才暴露的错误：路线格式不对、某步没有 check、
期望写成了主题词（「创建成功」）而不是裁判能从页面上读到的事实、intent.md 里偷偷写了步骤、intent.md 没有可供挑选的 name/description。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = sorted((ROOT / "scenarios").glob("*/expect.yaml"))

# 一步只允许这两个键。多一个键就是把"怎么取证"漏进了"验什么"。
ALLOWED_STEP_KEYS = {"go", "check"}

# 主题词：一条期望如果只剩这些词，裁判就有空间自己定义"什么叫成功"——
# 那正是我们要避免的。
VAGUE = (
    "成功", "正常", "正确", "没问题", "无误", "生效", "ok", "OK",
    "success", "successful", "successfully", "works", "correct",
)


def too_short(text: str) -> bool:
    """中文按字数算，西文按词数算。"""
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    return len(text.replace(" ", "")) < 14 if cjk else len(text.split()) < 6


def check(path: Path) -> list[str]:
    errs: list[str] = []
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rel = path.relative_to(ROOT)

    if not str(doc.get("goal", "")).strip():
        errs.append(f"{rel}: 缺 goal")

    steps = doc.get("steps")
    if not isinstance(steps, list) or not steps:
        errs.append(f"{rel}: steps 必须是非空列表")
        return errs

    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            errs.append(f"{rel}: 第 {i} 步不是一个映射")
            continue
        if not str(step.get("go", "")).strip():
            errs.append(f"{rel}: 第 {i} 步没有 go")
        for key in step:
            if key in ALLOWED_STEP_KEYS:
                continue
            hint = (
                "——refresh 已废弃：裁判每步都自己加载页面，干净读是协议里的不变式；"
                "真需要多加载一次就把这句话写进 go"
                if key == "refresh"
                else "——一步只有 go 和 check 两个键"
            )
            errs.append(f"{rel}: 第 {i} 步有多余的键 {key!r}{hint}")
        checks = step.get("check")
        if not isinstance(checks, list) or not checks:
            errs.append(f"{rel}: 第 {i} 步没有 check")
            continue
        for j, c in enumerate(checks, 1):
            if not isinstance(c, str) or not c.strip():
                errs.append(f"{rel}: 第 {i} 步第 {j} 条 check 必须是非空字符串")
                continue
            if any(v in c for v in VAGUE) and too_short(c):
                errs.append(
                    f"{rel}: 第 {i} 步第 {j} 条 check 像主题词而不是可读事实: {c!r}"
                )
    return errs


STEP_ENUM_RE = re.compile(r"^\s*(\d+)[.、]\s", re.M)
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
MAX_ONE_LINER = 90          # 一句完整的话：被测的是什么流程、做什么、验的是哪个问题。触发语不放这里


def check_frontmatter(path: Path, text: str) -> list[str]:
    """intent.md 开头要有 name + description 的 frontmatter，和 SKILL.md 一样——
    runner 靠它挑场景，人靠它知道这个目录在验什么。"""
    rel = path.relative_to(ROOT)
    m = FM_RE.match(text)
    if not m:
        return [f"{rel}: 开头缺 frontmatter（---\\nname: …\\ndescription: …\\n---），没有它就没法挑场景"]
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return [f"{rel}: frontmatter 不是合法 YAML：{e}"]
    errs = []
    if fm.get("name") != path.parent.name:
        errs.append(f"{rel}: frontmatter 的 name 应该等于目录名 {path.parent.name!r}，实际是 {fm.get('name')!r}")
    desc = str(fm.get("description") or "").strip()
    n = sum(1 for ch in desc if "一" <= ch <= "鿿") or len(desc.split())
    if not desc:
        errs.append(f"{rel}: description 缺失——它是 scripts/scenarios.py 列出来的那一行，没有它就没法挑场景")
    elif n < 25:
        errs.append(f"{rel}: description 只有 {n} 字，像个动作片段——要说清被测的是什么流程、做什么、验的是哪个问题")
    elif n > MAX_ONE_LINER:
        errs.append(f"{rel}: description {n} 字，超过 {MAX_ONE_LINER}——一句话说清流程、动作、验什么就够，触发语放正文「## 什么时候跑」")
    if "## 什么时候跑" not in text:
        errs.append(f"{rel}: 缺「## 什么时候跑」——用户说哪些话该跑它，写在这里而不是 description 里")
    return errs


def check_intent(path: Path) -> list[str]:
    """intent.md 不许写步骤——那是 playbook.md 的活，写在这里就是两份要同步的路径。"""
    if not path.exists():
        return [f"{path.relative_to(ROOT)}: 缺 intent.md"]
    text = path.read_text(encoding="utf-8")
    fm_errs = check_frontmatter(path, text)
    text = FM_RE.sub("", text, count=1)
    body = re.sub(r"```.*?```", "", text, flags=re.S)          # 代码块里的 yaml 不算
    n = len(STEP_ENUM_RE.findall(body))
    if n >= 3:
        fm_errs.append(f"{path.relative_to(ROOT)}: 出现 {n} 条「1. 2. 3.」式步骤枚举——步骤是 playbook.md 的活，intent.md 只放目标、参数、红线、造数、清理")
    return fm_errs


CONTEXT_REF_RE = re.compile(r"\bcontext\.([A-Za-z_][A-Za-z0-9_]*)")
NOT_A_KEY = {"yaml", "yml", "xxx"}          # 「context.yaml」是文件名，不是引用
FACTS_HEADING = "## 留给裁判的事实"


def context_refs(expect: dict) -> set[str]:
    """验收路线里引用了哪些 context.xxx（只认 steps 里的，注释不算）。"""
    keys: set[str] = set()
    for step in expect.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for text in [step.get("go", ""), *(step.get("check") or [])]:
            keys.update(k for k in CONTEXT_REF_RE.findall(str(text)) if k not in NOT_A_KEY)
    return keys


def declared_facts(intent_text: str) -> set[str]:
    """intent.md「留给裁判的事实」那一节里人点过名的键。"""
    section = ""
    if FACTS_HEADING in intent_text:
        tail = intent_text.split(FACTS_HEADING, 1)[1]
        section = tail.split("\n## ", 1)[0]
    return set(re.findall(r"^\s*-?\s*`?([A-Za-z_][A-Za-z0-9_]*)`?\s*:", section, re.M))


def check_context_pairing(expect_path: Path) -> list[str]:
    """验收路线引用的变量必须在 intent.md 的「留给裁判的事实」里声明过。

    这是**成对**的一根线，缺一半的后果很重：runner 拿不到"要交哪些值"的清单、
    裁判取不到证，整场判 BLOCK（judge.py 里"context.yaml 里没有 xxx"是最大单一失败原因）。
    它静态可知，就该在这里拦住，而不是等烧完一次浏览器跑批才发现。
    反向（声明了却没引用）只警告不拦——有些值是 runner 侧要用的，不必都出现在验收路线里。
    """
    try:
        expect = yaml.safe_load(expect_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    refs = context_refs(expect)
    if not refs:
        return []
    intent_path = expect_path.parent / "intent.md"
    if not intent_path.exists():
        return []
    declared = declared_facts(intent_path.read_text(encoding="utf-8"))
    missing = sorted(refs - declared)
    if not missing:
        return []
    listed = "、".join(f"`{k}`" for k in missing)
    return [f"{expect_path.relative_to(ROOT)}: 引用了 {listed}，但 intent.md 的「{FACTS_HEADING[3:]}」"
            f"里没有声明——runner 不会主动交这个值，裁判取不到就判 BLOCK。"
            f"在该节补上同名的一行，或把写死的值直接写进验收路线。"]


def main() -> int:
    if not SCENARIOS:
        print("scenarios/ 下没有找到任何场景")
        return 1
    bad = 0
    for path in SCENARIOS:
        errs = check(path) + check_intent(path.parent / "intent.md") + check_context_pairing(path)
        print(f"  {'ok  ' if not errs else '失败'} {path.parent.relative_to(ROOT)}/  (expect.yaml + intent.md)")
        for e in errs:
            print(f"       {e}")
        bad += bool(errs)
    print(f"\n{len(SCENARIOS) - bad}/{len(SCENARIOS)} 个场景格式合规")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
