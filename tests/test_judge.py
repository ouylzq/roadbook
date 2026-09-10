#!/usr/bin/env python3
"""scripts/judge.py 的合成用例。不需要 pytest、不联网、不开浏览器。

    python3 tests/test_judge.py

每个用例都先构造一份与演示场景 expect.yaml 镜像的 judgment.yaml，然后**只破坏一处**，
再断言退出码。这就是记分器的底线：绝不能把一份不完备、不镜像的判决换算成 PASS。
"""
import copy
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
JUDGE = ROOT / "scripts" / "judge.py"
SCENARIO = ROOT / "scenarios" / "todo-persistence"

PASS, FAIL, BLOCK = 0, 1, 2
REF_RE = re.compile(r"\bcontext\.([A-Za-z_][A-Za-z0-9_]*)")


def referenced(expect: dict) -> set[str]:
    """expect.yaml 里用到的 context.* 键。"""
    keys: set[str] = set()
    for s in expect["steps"]:
        for text in [s["go"]] + list(s["check"]):
            keys.update(REF_RE.findall(str(text)))
    return keys


def mirror(expect: dict) -> dict:
    """一份格式正确、全部通过的判决。"""
    return {
        "scenario": "todo-persistence",
        "steps": [
            {
                "go": s["go"],
                "reached": True,
                "how": "navigate 后刷新，用 get_page_text 读取",
                "check": [
                    {"fact": c, "result": "pass", "evidence": "引用的页面原文"}
                    for c in s["check"]
                ],
            }
            for s in expect["steps"]
        ],
    }


def build_cases(expect: dict) -> dict:
    cases: dict[str, tuple[dict | None, int, str]] = {}

    cases["全部通过"] = (mirror(expect), PASS, "完整镜像且带证据 → PASS")

    j = copy.deepcopy(mirror(expect))
    j["steps"][0]["check"][0].update(result="fail", evidence="还没有任务。")
    cases["一条fail"] = (j, FAIL, "带证据的单条 fail → FAIL")

    j = copy.deepcopy(mirror(expect))
    j["steps"][1]["check"][0]["evidence"] = ""
    cases["pass无证据"] = (j, BLOCK, "pass 却没有证据，无法记分")

    j = copy.deepcopy(mirror(expect))
    j["steps"][1]["reached"] = False
    for c in j["steps"][1]["check"]:
        c.update(result="blocked", evidence="", note="页面没加载出来")
    cases["某步未到达"] = (j, BLOCK, "到不了的步是 blocked，不是 fail")

    j = copy.deepcopy(mirror(expect))
    j["steps"][1]["reached"] = False  # check 仍是 pass
    cases["未到达却pass"] = (j, BLOCK, "没到达的步不许给 pass")

    j = copy.deepcopy(mirror(expect))
    j["steps"].pop()
    cases["漏一步"] = (j, BLOCK, "漏走步骤不算判决")

    j = copy.deepcopy(mirror(expect))
    j["steps"][0]["check"].pop()
    cases["漏一条check"] = (j, BLOCK, "漏答 check 不算判决")

    j = copy.deepcopy(mirror(expect))
    j["steps"][0]["go"] = "去了别的地方"
    cases["go被改写"] = (j, BLOCK, "路线不许改写")

    j = copy.deepcopy(mirror(expect))
    j["steps"][0]["check"][0]["fact"] = "换成更容易证明的说法"
    cases["fact被改写"] = (j, BLOCK, "期望不许改写")

    j = copy.deepcopy(mirror(expect))
    j["steps"][0]["check"][0]["result"] = "应该没问题"
    cases["result非法"] = (j, BLOCK, "只有 pass/fail/blocked 是判决")

    j = copy.deepcopy(mirror(expect))
    del j["steps"][0]["reached"]
    cases["缺reached"] = (j, BLOCK, "必须声明到没到达")

    cases["没交judgment"] = (None, BLOCK, "裁判什么都没交")

    # 引用的值不全：判决本身完美镜像，但 context.yaml 少了路线引用的键
    cases["缺context键"] = (mirror(expect), BLOCK, "context.yaml 在，但少了路线引用的那个键")
    return cases


def run_case(name: str, judgment: dict | None, expected: int, why: str) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir()
        if name == "环境阻塞":
            (run_dir / "blocked.txt").write_text("人机验证被触发", encoding="utf-8")
        # 路线引用到的 context 值默认都给上——只有专门测"缺值"的用例才故意少给
        keys = sorted(referenced(EXPECT))
        if keys:
            if name == "缺context键":
                keys = keys[:-1]
            (run_dir / "context.yaml").write_text(
                yaml.safe_dump({k: "x" for k in keys} or {}, allow_unicode=True), encoding="utf-8")
        if judgment is not None:
            with (run_dir / "judgment.yaml").open("w", encoding="utf-8") as f:
                yaml.safe_dump(judgment, f, allow_unicode=True, sort_keys=False)
        proc = subprocess.run(
            [sys.executable, str(JUDGE), str(SCENARIO), str(run_dir)],
            capture_output=True, text=True,
        )
        ok = proc.returncode == expected
        print(f"  {'ok  ' if ok else '失败'} {name:14s} 退出码={proc.returncode}（期望 {expected}）  {why}")
        if not ok:
            print("       ---- 记分器输出 ----")
            print("       " + (proc.stdout or proc.stderr).replace("\n", "\n       "))
        return ok


EXPECT = yaml.safe_load((SCENARIO / "expect.yaml").read_text(encoding="utf-8"))


def main() -> int:
    expect = EXPECT
    cases = build_cases(expect)
    # 环境阻塞这一类根本不需要 judgment 文件
    cases["环境阻塞"] = (None, BLOCK, "runner 标记环境问题，裁判没起")

    print(f"judge.py 对照 {SCENARIO.relative_to(ROOT)}，共 {len(cases)} 个用例")
    results = [run_case(n, j, e, w) for n, (j, e, w) in cases.items()]
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
