"""L1.1 — 铺根骨架（落盘步骤）

为什么：
  根项创建只留这一份实现，CLI 与技能共用，避免两套落盘逻辑漂移
  只建缺失、不覆盖：采用者已有内容比生成器更权威
  已知根项冲突先拒绝，不写入；检查后的 IO 失败仍不提供事务回滚
真实流程：
  根项清单 → 既有项预检 → 目标目录；目录 mkdir、文件 touch；已存在项跳过
概念：
  只建缺失、不覆盖；类型不符报错；dry 只记录不落盘
  报错文案与「（填充占位）」是 CLI 英文翻译的协议 token：改文案必须同步 core_message
跑：
  由 CLI 入口调用；公开技能复用同一实现
入：
  items / root / dry
出：
  (created, skipped, errors)；部分失败不回滚，修正后可重跑
"""
from pathlib import Path

from common.textio import write_lf

from .L0_1_data import ROOT_HIDDEN_DIRS, ROOT_HIDDEN_FILES


def _ensure_root(root, dry, created):
    """目标根不存在时创建（dry 只记录）。"""
    if not root.exists():
        if not dry:
            root.mkdir(parents=True)
        created.append(f"{root}/")


def _apply_items(items, root, dry, created, skipped, errors):
    """可见根项：目录 mkdir / 文件 touch；已存在只记录。"""
    for item in items:
        # 尾斜杠是「目录项」的编码；去掉后再与文件系统实际类型比对。
        is_dir = item.endswith("/")
        p = root / item.rstrip("/")
        if p.exists():
            if p.is_dir() != is_dir:
                errors.append(f"类型不符：{item}（已存在{'目录' if p.is_dir() else '文件'}）")
            else:
                skipped.append(item)
            continue
        if not dry:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.mkdir() if is_dir else p.touch()
        created.append(item)


def _apply_hidden_files(root, dry, created, skipped, errors):
    """隐藏文件：只建缺失；0 字节占位可填充，非空文件不覆盖。"""
    for name, content in ROOT_HIDDEN_FILES.items():
        p = root / name
        if p.exists():
            if p.is_file() and p.stat().st_size == 0:
                # 用户可能先 touch 了空文件；此时补默认内容，不算覆盖非空文件。
                if not dry:
                    write_lf(p, content)
                created.append(f"{name}（填充占位）")
            elif p.is_file():
                skipped.append(name)
            else:
                errors.append(f"类型不符：{name}（已存在目录）")
            continue
        if not dry:
            write_lf(p, content)
        created.append(name)


def _apply_hidden_dirs(root, dry, created, skipped, errors):
    """隐藏目录：只建缺失；目录内补 .gitkeep。"""
    for name in ROOT_HIDDEN_DIRS:
        d = root / name
        if d.exists():
            if d.is_dir():
                skipped.append(f"{name}/")
            else:
                errors.append(f"类型不符：{name}/（已存在文件）")
            continue
        if not dry:
            d.mkdir()
            (d / ".gitkeep").touch()
        created.append(f"{name}/")


def preflight_root(items, root):
    """写入前检查已有根项；不把项目集合或别的技术栈静默补成默认骨架。

    只看直接子项和类型，不读已有文件内容；隐藏项仍由根闸检查预算。
    允许已有 CLAUDE.md 适配入口，但生成器不创建它。
    """
    root = Path(root)
    if not root.exists():
        return []
    if not root.is_dir():
        return [f"目标不是目录：{root}"]
    expected = {item.rstrip("/"): item.endswith("/") for item in items}
    expected.update({name: False for name in ROOT_HIDDEN_FILES})
    expected.update({name: True for name in ROOT_HIDDEN_DIRS})
    errors = []
    for path in sorted(root.iterdir()):
        name = path.name
        if name in expected:
            if path.is_dir() != expected[name]:
                item = name + ("/" if expected[name] else "")
                errors.append(f"类型不符：{item}（已存在{'目录' if path.is_dir() else '文件'}）")
        elif not name.startswith(".") and not (name == "CLAUDE.md" and path.is_file()):
            errors.append(f"计划外根项：{name}（请确认项目目标与完整计划）")
    return errors


def apply_root(items, root, dry=False):
    """真正建根项：按「根目录 → 可见项 → 隐藏文件 → 隐藏目录」顺序，只建缺失项，不覆盖已有文件。

    已知根项冲突先拒绝；检查后中途出错不回滚，已创建项保留。
    """
    root = Path(root)
    errors = preflight_root(items, root)
    if errors:
        return [], [], errors
    created, skipped, errors = [], [], []
    _ensure_root(root, dry, created)
    _apply_items(items, root, dry, created, skipped, errors)
    _apply_hidden_files(root, dry, created, skipped, errors)
    _apply_hidden_dirs(root, dry, created, skipped, errors)
    return created, skipped, errors
