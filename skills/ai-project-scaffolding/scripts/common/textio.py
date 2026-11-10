"""L0 — 文本读写（写侧统一 LF）

为什么：
  文本读写只留这一处实现，避免各工具各自处理换行与编码
  写侧强制 LF：跨平台构建与 --check 才不会在干净 checkout 上假漂移
  读侧不加“偷偷改字节”的额外处理，需要原字节时直接用 Path.read_bytes
真实流程：
  读：path → UTF-8 文本（通用换行读取）
  写：path / text → 建父目录 → 写 UTF-8 + LF
概念：
  Windows 默认 CRLF 会让 `--check` 在干净 checkout 上假漂移；只有 write_lf 强制 LF。
  read_text 遵循 Python 文本模式，CRLF / CR 会转为 LF；需要原字节时用 Path.read_bytes。
跑：
  由根项创建逻辑与发布工具 import
入：
  Path / str
出：
  str / 写入副作用
"""
from __future__ import annotations

from pathlib import Path


def read_text(path: Path) -> str:
    """读 UTF-8 文本并按通用换行处理；原字节读取应使用 Path.read_bytes。"""
    return Path(path).read_text(encoding="utf-8")


def write_lf(path: Path, text: str) -> None:
    """写 UTF-8 文本并强制 LF；自动建父目录。

    不变量：同一文本在 Windows 与 Linux 写出相同字节（路径除外）。
    失败语义：父目录不可建或文件不可写时直接抛出 OSError，由调用方决定回滚或报告。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
