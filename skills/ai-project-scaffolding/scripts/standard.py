"""V1 根骨架入口：英文执行接口，中文注释；根段判据来自同一套数据表。

为什么：
  只留一个 CLI、人/AI 两条分支，避免两套实现与两套判据
  V1 只发根骨架：细骨架与细闸留 V2，先把采用者最常走的路径走稳
  入口只做参数、报告与退出码；判档、创建、闸各自成模块，便于单独审阅

三个子命令：
  tier       十二问判档；--plan 只读计划，--apply 创建根项，--dry 预演
  check-root 只查根项 / 槽位 / 类型 / 隐藏预算 / 根 Markdown 白名单
  human      交互向导：十二问 → 确认 → 创建 → 根闸

退出码：0 成功；1 操作或校验失败；2 用法错误。
JSON 默认英文、不附带 _zh 重复字段；中文只作为输入别名。
"""
import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
SRC = Path(__file__).resolve().parent
# 扁平 sys.path 注入：scripts/ 下平铺 common / scaffold_core / tier_pipeline / gate_pipeline。
sys.path.insert(0, str(SRC))
# 控制台码页可能是 GBK 等：输出流统一 UTF-8，保证诊断与路径不乱码（协议文本本身仍英文）。
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

from tier_pipeline.L0_1_data import CAP, HIDDEN_CAP, TRIGGERS
from tier_pipeline.L1_1_tier import resolve
from scaffold_core.L1_1_root import apply_root, preflight_root
from scaffold_core.L0_1_data import ROOT_HIDDEN_FILES, ROOT_HIDDEN_DIRS
from gate_pipeline.L2_1_root_gate import check_root_only

VERSION = "1.0.0"
TIERS = {"小": "small", "中": "medium", "大": "large"}
SLOT_NAMES = {"构建锚点": "build anchor", "依赖槽": "dependency slot", "自由槽": "free slot"}
# 档位别名：英文值 ↔ 中文键；同一条数据两向都能查。
TIER_ALIASES = {**{value: key for key, value in TIERS.items()}, **{key: key for key in TIERS}}
# 触发条件 → (公开 ID, 英文问句, 升级理由)；中文键只用于输入兼容，判据仍来自数据表。
TRIGGER_TEXT = {
    "协作": ("collaboration", "Will a second person read or edit this repository (excluding AI)?", "A separate AGENTS.md makes the working agreement shareable."),
    "用例多": ("test-suite", "Will regression tests exceed three cases, or need an independent test suite?", "A separate tests/ directory makes the suite independently runnable."),
    "外部示例": ("external-examples", "Will people outside this repository copy or view concrete examples?", "Keep external examples in examples/ rather than mixing them into docs/."),
    "文档多": ("many-docs", "Will there be at least four prose documents besides README?", "The docs/ directory needs indexing and categories."),
    "公开": ("public", "Will the repository be public, for example on GitHub?", "Public distribution needs a license and governance files."),
    "多入口": ("multiple-entrypoints", "Will there be a second executable entry point or at least five subcommands?", "README alone cannot describe several entry points clearly."),
    "资产": ("shipped-assets", "Must assets ship with the product (images, fonts, models, or sample data)?", "Shipped assets need a build anchor and an output location; their location remains flexible."),
    "构建": ("build", "Does the project need compilation, packaging, or release artifacts?", "A build anchor belongs at the root."),
    "分层": ("layering", "Will code exceed 2,000 lines, or support at least two platforms?", "The source needs adapter, module, and contract layers."),
    "文档超12": ("over-12-docs", "Will there be more than twelve prose documents?", "Organize docs/ into subdirectories."),
    "CI": ("ci", "Will CI or a release pipeline run against a remote repository?", "CI needs workflow configuration and release scripts."),
    "硬软双栈": ("firmware-and-host", "Will both firmware and host software be delivered?", "Two products need a root build anchor and layered source; assets still use the free slot."),
}
TRIGGER_ALIASES = {**{row[0]: key for key, row in TRIGGER_TEXT.items()}, **{key: key for key in TRIGGER_TEXT}}
SUBSTITUTION = "Public medium tier: LICENSE.txt replaces examples/; keep examples under docs/."
def core_message(text):
    """把根段内部的中文报告翻译成英文协议。

    匹配顺序：先查 fixed 精确表，再按 patterns 顺序做 fullmatch；未知报告保留原文并加
    `Root operation diagnostic:` 前缀，避免本地化吞掉排错依据。

    维护契约：新增或修改根段中文文案时，必须同时在这里加对应英文模板；
    否则会落到未知分支，协议里会出现中文或原始诊断。
    """
    patterns = [
        (r"缺根项：(.*?)（([小中大])档应为 (.*?)）", lambda m: f"Missing root entries: {m[1]}; {TIERS[m[2]]} tier requires {m[3]}"),
        (r"缺根项：(.*?)（([小中大])档固定项）", lambda m: f"Missing fixed root entries: {m[1]}; tier: {TIERS[m[2]]}"),
        (r"多根项：(.*?)（([小中大])档上限 (\d+) 项；域外根项本轮不建）", lambda m: f"Unexpected root entries: {m[1]}; {TIERS[m[2]]} tier allows at most {m[3]} visible entries"),
        (r"多根项：(.*?)（([小中大])档上限 (\d+) 项）", lambda m: f"Unexpected root entries: {m[1]}; {TIERS[m[2]]} tier allows at most {m[3]} visible entries"),
        (r"根项类型不符：(.*?)（目录项应是目录，文件项应是文件）", lambda m: f"Wrong root entry type: {m[1]}; directory slots require directories and file slots require files"),
        (r"根项类型不符：(.*?)（构建锚点应是文件；依赖槽按候选类型，DEPS 是文件；自由槽应是目录）", lambda m: f"Wrong root entry type: {m[1]}; build anchors and DEPS must be files; other dependency slots and free slots must be directories"),
        (r"(缺根项|多根项)：(构建锚点|依赖槽|自由槽)必须恰好一个（候选：(.*?)）", lambda m: f"{'Missing' if m[1] == '缺根项' else 'Extra'} slot entry: exactly one {SLOT_NAMES[m[2]]} is required; candidates: {m[3]}"),
        (r"隐藏项 (\d+) > (\d+)（含 .git；多出的：(.*?)）", lambda m: f"Hidden entry budget exceeded: {m[1]} > {m[2]} including .git; counted entries: {m[3]}"),
        (r"根 .md 非白名单：(.*?)（只许 README.md / AGENTS.md / CLAUDE.md）", lambda m: f"Root Markdown files outside the allowlist: {m[1]}; only README.md / AGENTS.md / CLAUDE.md are allowed"),
        (r"根段档位 = ([小中大])（可见 (\d+)/(\d+)，隐藏 (\d+)/(\d+)；机器产物豁免 (\d+)）", lambda m: f"Root tier = {TIERS[m[1]]}; visible {m[2]}/{m[3]}, hidden {m[4]}/{m[5]}; machine-generated entries exempted: {m[6]}"),
        (r"根项 = (.*)", lambda m: f"Root entries = {m[1]}"),
        (r"第 6 项 = (.*)", lambda m: f"Sixth entry = {m[1]}"),
        (r"槽位 = 构建 (.*?) / 依赖 (.*?) / 自由 (.*)", lambda m: f"Slots = build {m[1]} / dependency {m[2]} / free {m[3]}"),
        (r"FAIL 根目录不存在：(.*)", lambda m: f"Root directory is missing or is not a directory: {m[1]}"),
        (r"FAIL 无法导入档位数据：(.*)", lambda m: f"Cannot load tier data: {m[1]}"),
        (r"类型不符：(.*?)（已存在(目录|文件)）", lambda m: f"Type conflict: {m[1]}; an existing {'directory' if m[2] == '目录' else 'file'} occupies this path"),
        (r"目标不是目录：(.*)", lambda m: f"Target is not a directory: {m[1]}"),
        (r"计划外根项：(.*?)（请确认项目目标与完整计划）", lambda m: f"Unplanned root entry: {m[1]}; confirm the project target and complete plan before writing"),
    ]
    fixed = {
        "缺根项：examples/ 或 LICENSE.txt 二选一（公开项目用 LICENSE.txt）": "Missing root entry: choose examples/ or LICENSE.txt; public projects use LICENSE.txt",
        "多根项：examples/ 与 LICENSE.txt 只能二选一": "Unexpected root entries: choose exactly one of examples/ and LICENSE.txt",
    }
    if text in fixed:
        return fixed[text]
    for pattern, render in patterns:
        match = re.fullmatch(pattern, text)
        if match:
            return render(match)
    # 未知源报告保留原始详情，避免本地化丢失排错依据。
    return f"Root operation diagnostic: {text}"



def question_rows():
    """只输出英文协议，不重复附带解释译文。"""
    return [dict(id=TRIGGER_TEXT[tid][0], ask=TRIGGER_TEXT[tid][1],
                 upgrade_to=TIERS[tier], why=TRIGGER_TEXT[tid][2])
            for tid, _, tier, _ in TRIGGERS]


def tier_parser():
    """tier 子命令参数：--trigger 可重复命中判档；--plan 与 --apply 互斥，查询/规划/预演均不落盘。"""
    parser = argparse.ArgumentParser(prog="ai-project-scaffold tier", description="Query, plan, or create a root skeleton")
    parser.add_argument("--trigger", action="append", default=[], help="Matched trigger ID; repeat as needed; see --list")
    parser.add_argument("--list", action="store_true", help="List the twelve questions")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--plan", action="store_true", help="Show the entry plan without writing")
    actions.add_argument("--apply", action="store_true", help="Create missing entries at the target")
    parser.add_argument("--root", help="Target directory; defaults to the current directory")
    parser.add_argument("--dry", "--dry-run", action="store_true", help="Preview --apply without writing")
    return parser


def tier_main(argv):
    """tier 子命令：--list 列十二问；否则判档并输出根项清单。

    --plan 只读计划；--apply 创建；--dry 只预演。查询 / 计划 / 预演都不落盘。
    errors 非空返回 1；参数组合非法由 argparse 以退出码 2 拒绝。
    """
    parser = tier_parser()
    args = parser.parse_args(argv)
    if args.dry and not args.apply:
        parser.error("--dry requires --apply")
    if args.list and (args.trigger or args.plan or args.apply or args.root or args.dry):
        parser.error("--list may only be combined with --json")
    if args.list:
        rows = question_rows()
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for row in rows:
                print(f"[{row['id']}] -> {row['upgrade_to']}: {row['ask']}")
        return 0
    # 先归一别名再判未知；避免中文/英文拼写差异被当成未知 ID。
    unknown = sorted(set(args.trigger) - set(TRIGGER_ALIASES))
    if unknown:
        parser.error(f"Unknown trigger IDs: {', '.join(unknown)}; see --list")
    hits = [TRIGGER_ALIASES[tid] for tid in args.trigger]
    tier, items, switched = resolve(hits)
    root = Path(args.root or Path.cwd()).resolve()
    # 对外只发英文协议字段；路径和原始错误保留实际内容。
    payload = dict(tier=TIERS[tier], visible=items, visible_cap=CAP[tier], hidden_cap=HIDDEN_CAP,
                   triggered=[dict(id=TRIGGER_TEXT[t][0], upgrade_to=TIERS[u]) for t, _, u, _ in TRIGGERS if t in hits],
                   substitution=SUBSTITUTION if switched else None, dry_run=args.dry)
    if args.plan:
        payload["plan"] = dict(root=str(root), visible=items,
                               hidden=list(ROOT_HIDDEN_FILES) + [name + "/" for name in ROOT_HIDDEN_DIRS],
                               errors=[core_message(e) for e in preflight_root(items, root)],
                               notes=["The generator uses fixed slot names; pyproject.toml is an empty build placeholder, not a Python stack decision.",
                                      "Default .gitignore includes Python patterns; review it for the project's actual toolchain."])
    errors = payload.get("plan", {}).get("errors", [])
    if args.apply:
        # 只有 --apply 才会碰文件系统；--plan / --list / --dry 保持只读。
        created, skipped, errors = apply_root(items, root, args.dry)
        # 创建清单里的中文占位标记对协议转英文；错误诊断不走此处，统一由 core_message 翻译。
        created = [name.replace("（填充占位）", " (filled placeholder)") for name in created]
        payload["apply"] = dict(root=str(root), created=created, skipped=skipped,
                                errors=[core_message(e) for e in errors])
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Tier: {TIERS[tier]}; visible {len(items)}/{CAP[tier]}; hidden budget {HIDDEN_CAP}")
        print("\n".join(f"  {item}" for item in items))
        if switched:
            print(SUBSTITUTION)
        if args.plan:
            print(f"Plan only, no writes: {root}; also create .gitignore / .gitattributes / .github/")
            print(json.dumps(payload["plan"], ensure_ascii=False, indent=2))
        if args.apply:
            print("Dry run; no writes" if args.dry else "Root creation finished; existing nonempty files preserved")
            print(json.dumps(payload["apply"], ensure_ascii=False, indent=2))
        print(f'Validate: python "{Path(__file__).resolve()}" check-root --tier {TIERS[tier]} --root "{root}"')
    return 1 if errors else 0


def check_main(argv):
    """根闸子命令：只查根项/槽位/类型/隐藏预算/根 .md 白名单；中文判据报告经 core_message 转英文协议。"""
    parser = argparse.ArgumentParser(prog="ai-project-scaffold check-root", description="Validate root entries, types, and budgets only")
    parser.add_argument("--tier", type=parse_tier, choices=list(TIERS.values()), required=True, help="small / medium / large; Chinese aliases accepted")
    parser.add_argument("--root", help="Target directory; defaults to the current directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)
    problems, notes, fatal = check_root_only(TIER_ALIASES[args.tier], args.root)
    # pass 只看 fatal / problems；notes 是摘要，不参与判定。
    # 同一问题可能由多个检查重复产生，按首次出现去重。
    payload = dict(mode="root", **{"pass": not fatal and not problems}, fatal=fatal or None,
                   notes=[core_message(n) for n in notes], problems=[core_message(e) for e in dict.fromkeys(problems)])
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("\n".join(payload["notes"] + payload["problems"]))
        print("Root validation passed" if payload["pass"] else "Root validation failed")
    return 0 if payload["pass"] else 1


def parse_tier(value):
    """兼容中文输入，帮助和结果只列英文协议值。"""
    try:
        return TIERS[TIER_ALIASES[value]]
    except KeyError:
        raise argparse.ArgumentTypeError(f"Unknown tier: {value}; choose small/medium/large") from None


def human_main(argv):
    """交互向导：十二问 → 输入 yes 确认 → 创建根项 → 自动过根闸；空目标或 EOF/中断返回 2。"""
    parser = argparse.ArgumentParser(prog="ai-project-scaffold human", description="Twelve questions -> confirmation -> root creation -> validation")
    parser.add_argument("--root", help="Target directory; ask if omitted")
    args = parser.parse_args(argv)
    try:
        root = args.root or input("Target directory (required): ").strip()
        if not root:
            print("Empty target; cancelled")
            return 2
        hits = []
        print("Count only current needs or needs certain within three months; answer yes/no")
        for row in question_rows():
            while True:
                answer = input(f"{row['ask']} [y/n]: ").strip().lower()
                if answer in {"y", "yes", "是", "n", "no", "否"}:
                    break
                print("Enter y or n")
            if answer in {"y", "yes", "是"}:
                hits.append(TRIGGER_ALIASES[row["id"]])
        tier, items, switched = resolve(hits)
        print(f"Target: {Path(root).resolve()}\nTier: {TIERS[tier]}\nRoot entries: {', '.join(items)}")
        if switched:
            print(SUBSTITUTION)
        print("Also create .gitignore / .gitattributes / .github/; empty hidden config files may receive defaults")
        if input("Confirm creation? Type yes: ").strip().lower() != "yes":
            print("Cancelled; nothing written")
            return 0
        _, _, errors = apply_root(items, root)
        if errors:
            print("\n".join(core_message(e) for e in errors))
            return 1
        return check_main(["--tier", TIERS[tier], "--root", root])
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled")
        return 2


def main(argv=None):
    """顶层分发：无参/-h 打印用法、--version 打印版本；未知命令退出 2；OSError 统一转退出 1（JSON 模式含 error=filesystem_error）。"""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv == ["--help"] or argv == ["-h"]:
        print("Usage: ai-project-scaffold {tier|check-root|human} [options]\nV1 root scaffolding only; Python 3.10+, no runtime dependencies")
        return 0
    if argv == ["--version"]:
        print(VERSION)
        return 0
    command = argv.pop(0)
    actions = {"tier": tier_main, "check-root": check_main, "human": human_main}
    if command not in actions:
        print(f"Unknown command: {command}; see --help", file=sys.stderr)
        return 2
    # 退出码约定：0 成功 / 1 操作失败 / 2 用法错误；OSError 统一转 1。
    try:
        return actions[command](argv)
    except OSError as exc:
        message = f"Filesystem operation failed (errno {exc.errno})"
        if "--json" in argv:
            print(json.dumps(dict(error="filesystem_error", message=message, detail=str(exc)), ensure_ascii=False))
        else:
            print(f"{message}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
