#!/usr/bin/env python3
"""校验触发样例结构; --run-plans 在隔离目录运行三个 CLI 计划样例, 不代表真实模型评测。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

# Windows 英文控制台默认 cp1252, 打印中文会 UnicodeEncodeError; 统一输出 UTF-8。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "skills/ai-project-scaffolding/evals/evals.json"
CLI = ROOT / "skills/ai-project-scaffolding/scripts/standard.py"


def string_list(value):
    """只接受非空字符串列表, 避免错误类型进入集合或子进程。"""
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v.strip() for v in value)


def validate(data):
    """结构错误统一转问题列表, 不抛类型异常; 功能样例只能是无写入计划。"""
    if not isinstance(data, dict):
        return ["顶层必须是对象"]
    trigger, cases = data.get("trigger"), data.get("functional")
    problems = []
    if data.get("skill") != "ai-project-scaffolding":
        problems.append("skill 名称不匹配")
    if not isinstance(trigger, dict):
        problems.append("trigger 必须是对象")
    else:
        pos, neg = trigger.get("should_trigger"), trigger.get("should_not_trigger")
        for name, values in [("should_trigger", pos), ("should_not_trigger", neg)]:
            if not string_list(values) or len(values) < 8:
                problems.append(f"{name} 至少需要 8 条非空字符串")
            elif len(set(values)) != len(values):
                problems.append(f"{name} 有重复")
        if string_list(pos) and string_list(neg) and set(pos) & set(neg):
            problems.append("正负样例有交集")
    if not isinstance(cases, list) or len(cases) != 3:
        return problems + ["functional 需要三个计划样例"]
    ids, tiers = [], []
    for case in cases:
        if not isinstance(case, dict):
            problems.append("功能样例必须是对象")
            continue
        args = case.get("args")
        if not string_list(args) or args[0] != "tier" or "--plan" not in args or "--json" not in args:
            problems.append("功能样例必须调用 tier --plan --json")
        elif any(arg == "--root" or arg.startswith("--root=") or arg in {"--apply", "--list"} for arg in args):
            problems.append("功能样例不得指定 --root / --apply / --list")
        if "expect_files" in case or case.get("expect_no_write") is not True:
            problems.append("计划样例须验证 expect_visible 和不写入, 不能要求落盘文件")
        if not string_list(case.get("expect_visible")):
            problems.append("expect_visible 必须是非空字符串列表")
        case_id, tier = case.get("id"), case.get("expect_tier")
        if not isinstance(case_id, str) or not case_id:
            problems.append("样例 id 必须是非空字符串")
        else:
            ids.append(case_id)
        if tier not in ("small", "medium", "large"):
            problems.append("expect_tier 必须是 small / medium / large")
        else:
            tiers.append(tier)
    if len(set(ids)) != 3 or set(tiers) != {"small", "medium", "large"}:
        problems.append("三个样例 id 必须唯一, 并覆盖三个档位")
    return problems


def run_plans(cases):
    """执行受限的计划命令, 检查完整根项集合、档位和无文件写入。"""
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    problems = []
    with tempfile.TemporaryDirectory(prefix="scaffold-plan-eval-") as tmp:
        base = Path(tmp)
        for case in cases:
            target = base / case["expect_tier"]
            result = subprocess.run([sys.executable, "-B", str(CLI), *case["args"], "--root", str(target)],
                                    cwd=base, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30)
            try:
                payload = json.loads(result.stdout)
                passed = (result.returncode == 0 and payload["tier"] == case["expect_tier"]
                          and sorted(v.rstrip("/") for v in payload["visible"]) == sorted(case["expect_visible"])
                          and payload["plan"]["visible"] == payload["visible"] and not target.exists())
            except (ValueError, KeyError, TypeError):
                passed = False
            if not passed:
                problems.append(f"计划样例失败: {case['id']}; exit={result.returncode}")
    return problems


def main():
    """默认只检查结构; 加 --run-plans 才执行 CLI, 两者均不调用模型。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, default=EVALS, help="Evaluation JSON file")
    parser.add_argument("--run-plans", action="store_true", help="Run isolated CLI plan cases (no model calls)")
    args = parser.parse_args()
    try:
        data = json.loads(args.evals.read_text(encoding="utf-8"))
        problems = validate(data)
        if not problems and args.run_plans:
            problems.extend(run_plans(data["functional"]))
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        problems = [f"评测读取或执行失败: {exc}"]
    if problems:
        print("FAIL evals")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    trigger = data["trigger"]
    print(f"PASS evals 结构: {len(trigger['should_trigger'])} 正 / {len(trigger['should_not_trigger'])} 负 / 3 计划")
    if args.run_plans:
        print("PASS 3/3 CLI 计划样例, 未写入目标; 真实模型行为未由此验证")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
