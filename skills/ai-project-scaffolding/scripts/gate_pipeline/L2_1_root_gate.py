"""L2.1 — 根层闸（只查仓根）

为什么：
  根闸只查能用机器判定的部分：根项、槽位、类型、隐藏预算、根 .md 白名单
  不越权查正文、文档质量或业务规则，那些留给人审
  档位规则从判档数据表来，本文件只做比对，不重列数字
真实流程：
  目标仓根 → 可见/隐藏项 → 与档位规则比对 → 类型、隐藏上限、根 .md 白名单
概念：
  根段只建占位；不查 docs / 正文 / 入口内容
  大档：构建锚点 / 依赖槽 / 自由槽各取一个（名字可变）
  中档：examples/ 或 LICENSE.txt 二选一（公开项目用后者）
跑：
  由 check-root 子命令调用
入：
  tier_name / root
出：
  (problems, notes, fatal)；fatal=True 表示只打印首条 FAIL
  注意：problems 里的中文是 CLI 英文翻译的协议 token，改文案必须同步 standard.py::core_message
"""
from pathlib import Path

from gate_pipeline.L0_1_common import (
    default_root, HIDDEN_EXEMPT, ROOT_MD_WHITELIST, ADAPTER_ROOT_FILES,
)
from gate_pipeline.L1_1_tier_adapter import load_tier, tier_spec


def _fmt(items):
    """集合 → 排序后的逗号串；空集显示破折号。"""
    return ", ".join(sorted(items)) or "—"


def _scan_root(root):
    """仓根 → 可见项 / 全部隐藏项 / 计入预算的隐藏项 / 非白名单 .md。

    - actual：可见根项；排除 . 开头项、__pycache__ 和适配层文件（CLAUDE.md 可占根，但不占可见名额）。
    - hidden_all：所有 . 开头项，用于报告「机器产物豁免」数量。
    - hidden：计入隐藏预算的隐藏项（HIDDEN_EXEMPT 不计）。
    - bad_md：根目录里不在白名单的 .md。
    """
    actual = {p.name for p in root.iterdir()
              if not p.name.startswith(".") and p.name != "__pycache__"
              and p.name not in ADAPTER_ROOT_FILES}
    hidden_all = sorted(p.name for p in root.iterdir() if p.name.startswith("."))
    hidden = [n for n in hidden_all if n not in HIDDEN_EXEMPT]
    bad_md = sorted(p.name for p in root.iterdir()
                    if p.is_file() and p.suffix == ".md"
                    and p.name not in ROOT_MD_WHITELIST)
    return actual, hidden_all, hidden, bad_md


def _check_exact(spec, actual, root, tier_name, cap, problems):
    """小档：精确根项集合。"""
    expected, dirs = spec["expected"], spec["dirs"]
    missing = expected - actual
    extra = actual - expected
    wrong = sorted(n for n in expected & actual
                   if (root / n).is_dir() != (n in dirs))
    if missing:
        problems.append(f"缺根项：{_fmt(missing)}（{tier_name}档应为 {_fmt(expected)}）")
    if extra:
        problems.append(f"多根项：{_fmt(extra)}（{tier_name}档上限 {cap} 项；域外根项本轮不建）")
    if wrong:
        problems.append(f"根项类型不符：{_fmt(wrong)}（目录项应是目录，文件项应是文件）")


def _check_alternative(spec, actual, root, tier_name, cap, problems, notes):
    """中档：固定项 + examples/ 或 LICENSE.txt 二选一。"""
    fixed, dirs, alt = spec["fixed"], spec["fixed_dirs"], spec["alt"]
    missing = fixed - actual
    rest = actual - fixed
    alt_hits = rest & set(alt)
    unknown = rest - alt_hits
    wrong = sorted(n for n in fixed & actual
                   if (root / n).is_dir() != (n in dirs))
    wrong += sorted(n for n in alt_hits if (root / n).is_dir() != alt[n])
    if missing:
        problems.append(f"缺根项：{_fmt(missing)}（{tier_name}档固定项）")
    if not alt_hits:
        problems.append("缺根项：examples/ 或 LICENSE.txt 二选一（公开项目用 LICENSE.txt）")
    if len(alt_hits) > 1:
        problems.append("多根项：examples/ 与 LICENSE.txt 只能二选一")
    if unknown:
        problems.append(f"多根项：{_fmt(unknown)}（{tier_name}档上限 {cap} 项）")
    if wrong:
        problems.append(f"根项类型不符：{_fmt(set(wrong))}（目录项应是目录，文件项应是文件）")
    if alt_hits:
        notes.append(f"第 6 项 = {_fmt(alt_hits)}")


def _check_slots(spec, actual, root, tier_name, cap, problems, notes):
    """大档：固定项 + 构建锚点 / 依赖槽 / 自由槽各一个。"""
    fixed, dirs = spec["fixed"], spec["fixed_dirs"]
    missing = fixed - actual
    rest = actual - fixed
    build = rest & spec["build"]
    dep = rest & spec["dep"]
    free = rest & spec["free"]
    unknown = rest - build - dep - free
    # 类型矩阵：构建锚点必须是文件；依赖槽默认是目录，dep_files 里的 DEPS 是文件；自由槽必须是目录。
    wrong = sorted(n for n in fixed & actual
                   if (root / n).is_dir() != (n in dirs))
    wrong += sorted(n for n in build if (root / n).is_dir())
    wrong += sorted(n for n in dep
                    if (root / n).is_dir() != (n not in spec["dep_files"]))
    wrong += sorted(n for n in free if not (root / n).is_dir())
    if missing:
        problems.append(f"缺根项：{_fmt(missing)}（{tier_name}档固定项）")
    if len(build) != 1:
        problems.append(
            f"{'缺根项' if not build else '多根项'}：构建锚点必须恰好一个"
            f"（候选：{_fmt(spec['build'])}）")
    if len(dep) != 1:
        problems.append(
            f"{'缺根项' if not dep else '多根项'}：依赖槽必须恰好一个"
            f"（候选：{_fmt(spec['dep'])}）")
    if len(free) != 1:
        problems.append(
            f"{'缺根项' if not free else '多根项'}：自由槽必须恰好一个"
            f"（候选：{_fmt(spec['free'])}）")
    if unknown:
        problems.append(f"多根项：{_fmt(unknown)}（{tier_name}档上限 {cap} 项）")
    if wrong:
        problems.append(f"根项类型不符：{_fmt(set(wrong))}（构建锚点应是文件；依赖槽按候选类型，DEPS 是文件；自由槽应是目录）")
    notes.append(f"槽位 = 构建 {_fmt(build)} / 依赖 {_fmt(dep)} / 自由 {_fmt(free)}")


def _check_hidden(hidden, hidden_cap, problems):
    """隐藏项上限；.git 计入但不豁免。"""
    if len(hidden) > hidden_cap:
        problems.append(f"隐藏项 {len(hidden)} > {hidden_cap}"
                        f"（含 .git；多出的：{_fmt(hidden)}）")


def _check_bad_md(bad_md, problems):
    """根 .md 只许三份白名单。"""
    if bad_md:
        problems.append(f"根 .md 非白名单：{_fmt(bad_md)}（只许 README.md / AGENTS.md / CLAUDE.md）")


def check_root_only(tier_name, root=None):
    """目标仓根 → (problems, notes, fatal)。

    fatal=True 只用于无法继续的情况（根目录不存在 / 档位数据导入失败 / 档位名未知）；
    其余规则问题放进 problems，由调用方一次报告。notes 是给人看的摘要，不参与 pass/fail。
    """
    root = Path(root).resolve() if root else default_root()
    if not root.is_dir():
        return [f"FAIL 根目录不存在：{root}"], [], True

    try:
        tier_mod = load_tier()
    except Exception as e:  # noqa: BLE001
        return [f"FAIL 无法导入档位数据：{e}"], [], True
    try:
        spec = tier_spec(tier_mod, tier_name)
    except ValueError as e:
        return [f"FAIL {e}"], [], True

    actual, hidden_all, hidden, bad_md = _scan_root(root)
    # 可见根项上限；与 STRUCT 的条目数一致（CAP 由 STRUCT 推导）。
    cap = tier_mod.CAP[tier_name]
    problems = []
    notes = [
        f"根段档位 = {tier_name}（可见 {len(actual)}/{cap}，"
        f"隐藏 {len(hidden)}/{tier_mod.HIDDEN_CAP}；机器产物豁免 {len(hidden_all) - len(hidden)}）",
        f"根项 = {_fmt(actual)}",
    ]

    # 三种 mode 由 L1_1_tier_adapter.tier_spec 产生：小档 exact / 中档 alternative / 大档 slots。
    if spec["mode"] == "exact":
        _check_exact(spec, actual, root, tier_name, cap, problems)
    elif spec["mode"] == "alternative":
        _check_alternative(spec, actual, root, tier_name, cap, problems, notes)
    else:  # slots（大档）
        _check_slots(spec, actual, root, tier_name, cap, problems, notes)

    _check_hidden(hidden, tier_mod.HIDDEN_CAP, problems)
    _check_bad_md(bad_md, problems)
    return problems, notes, False
