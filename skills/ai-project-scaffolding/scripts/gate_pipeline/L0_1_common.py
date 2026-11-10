"""V1 根骨架的根闸公共常量（从开发源裁剪的根段投影）。

为什么：
  闸的公共常量单独一层，根闸与适配器共用，避免各写一份
  隐藏豁免、根 .md 白名单、适配入口集中在这里，审阅只需看一处
  CLAUDE.md 只作可选适配入口：不自动创建，也不占可见根项
真实流程：
  根闸读取根目录 → 用这些常量区分可见项 / 隐藏项 / 根 Markdown
概念：
  HIDDEN_EXEMPT 是不计入隐藏预算的机器 / 本地产物
  ROOT_MD_WHITELIST 允许 README.md / AGENTS.md / CLAUDE.md
  ADAPTER_ROOT_FILES 里的 CLAUDE.md 是适配层入口，不计入可见根项
跑：
  由 L2_1_root_gate 导入
入：
  无
出：
  default_root / HIDDEN_EXEMPT / ROOT_MD_WHITELIST / ADAPTER_ROOT_FILES
"""
from pathlib import Path


def default_root():
    """未传 --root 时体检当前目录；调用时取，不在 import 时固化。"""
    return Path.cwd()

HIDDEN_EXEMPT = {
    # 机器 / 本地环境产物：不计入隐藏项预算。
    ".venv", ".env", ".env.local", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", ".idea", ".vscode", ".gitkeep",
    ".DS_Store", "Thumbs.db",
}

ROOT_MD_WHITELIST = {
    # 根目录允许出现的 Markdown 文件；除此之外的根 .md 会被根闸判红。
    "README.md", "AGENTS.md", "CLAUDE.md",
}

ADAPTER_ROOT_FILES = {
    # 适配层文件：允许占根，但不计入可见根项；目前只有 CLAUDE.md。
    "CLAUDE.md",
}
