"""L1.1 — 档位适配（把档位数据表变成闸可用的集合）

为什么：
  闸不复制三档清单，改为从判档数据表推导，防止两处数字漂移
  惰性 import + 路径回退：源码树与安装包两种布局共用同一份实现
真实流程：
  惰性 import tier_pipeline.L0_1_data → STRUCT/CAP/HIDDEN_CAP → 期望根项集合
概念：
  数据表是唯一真相源；闸不复制三档清单
跑：
  由 L2.1 根层闸调用
入：
  档位名（小/中/大）
出：
  数据表模块 / 档位规则
"""
import sys
from pathlib import Path


def load_tier():
    """惰性 import 数据表；扁平布局回退到 scripts/，不依赖 cwd。"""
    try:
        from tier_pipeline import L0_1_data
        return L0_1_data
    except ImportError:
        p = str(Path(__file__).resolve().parents[1])
        if p not in sys.path:
            sys.path.insert(0, p)
        from tier_pipeline import L0_1_data
        return L0_1_data


def _norm(items):
    """根项去尾斜杠 → 集合。"""
    return {x.rstrip("/") for x in items}


def _dirs(items):
    """只取目录项（尾斜杠）并去尾斜杠。"""
    return {x.rstrip("/") for x in items if x.endswith("/")}


def tier_spec(tier_mod, tier_name):
    """根层闸用的档位规则。

    返回三种 schema，由 L2_1_root_gate 按 `mode` 分派：
    - exact：`{expected, dirs}`；小档精确集合。
    - alternative：`{fixed, fixed_dirs, alt}`；中档固定项 + `examples/` 或 `LICENSE.txt` 二选一。
    - slots：`{fixed, fixed_dirs, build, dep, dep_files, free}`；大档固定项 + 三个槽位各取一个。
      `dep_files` 标记依赖槽里按文件存在的候选（DEPS），其余依赖槽按目录。
    """
    if tier_name not in tier_mod.STRUCT:
        raise ValueError(f"未知档位：{tier_name}（可选：{'/'.join(tier_mod.STRUCT)}）")
    items = tier_mod.STRUCT[tier_name]
    expected = _norm(items)
    dirs = _dirs(items)

    if tier_name == "大":
        build = _norm(tier_mod.BUILD_ANCHORS)
        dep = _norm(tier_mod.DEP_SLOTS)
        free = _norm(tier_mod.FREE_SLOT)
        fixed = expected - (build | dep | free)
        return {
            "mode": "slots",
            "fixed": fixed,
            "fixed_dirs": fixed & dirs,
            "build": build,
            "dep": dep,
            "dep_files": dep & _norm(tier_mod.DEP_FILE_SLOTS),
            "free": free,
        }

    if tier_name == "中":
        fixed = expected - {"examples"}
        return {
            "mode": "alternative",
            "fixed": fixed,
            "fixed_dirs": fixed & dirs,
            "alt": {"examples": True, "LICENSE.txt": False},  # 名字 -> 是否目录
        }

    return {"mode": "exact", "expected": expected, "dirs": dirs}
