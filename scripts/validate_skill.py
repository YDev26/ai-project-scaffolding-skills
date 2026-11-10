#!/usr/bin/env python3
"""validate_skill.py — 公开技能仓的最小结构校验（仅标准库）

检查：
  - skills/<name>/SKILL.md 存在，frontmatter 以 --- 包裹；
  - name kebab-case、≤64、与目录同名；
  - description 1..1024 字符，不含 < >；
  - license / compatibility 存在；
  - 正文 <500 行；
  - SKILL.md 内相对链接指向存在的文件；
  - references/ scripts/ assets/templates/ 关键文件存在。

用法：python scripts/validate_skill.py
退出码：0=通过；1=有问题。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
REQUIRED_FIELDS = ("name", "description", "license", "compatibility")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["frontmatter 未以 --- 开始"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text, ["frontmatter 缺少结束 ---"]

    data: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.startswith((" ", "\t", "#")):
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    body = "\n".join(lines[end + 1:])
    return data, body, errors


def check_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return [f"缺 SKILL.md：{md}"]
    text = md.read_text(encoding="utf-8")
    fm, body, parse_errors = parse_frontmatter(text)
    errors.extend(parse_errors)

    for key in REQUIRED_FIELDS:
        if not fm.get(key):
            errors.append(f"缺 frontmatter 字段：{key}")

    name = fm.get("name", "")
    if name:
        if not NAME_RE.match(name):
            errors.append(f"name 不是 kebab-case：{name}")
        if len(name) > 64:
            errors.append(f"name 超过 64 字符：{len(name)}")
        if name != skill_dir.name:
            errors.append(f"name（{name}）≠ 目录名（{skill_dir.name}）")

    desc = fm.get("description", "")
    if desc:
        if len(desc) > 1024:
            errors.append(f"description 超过 1024 字符：{len(desc)}")
        if "<" in desc or ">" in desc:
            errors.append("description 不能包含 < 或 >")

    if len(body.splitlines()) >= 500:
        errors.append(f"正文行数 {len(body.splitlines())} ≥ 500")

    for target in LINK_RE.findall(body):
        target = target.split("#", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (skill_dir / target).exists():
            errors.append(f"链接指向不存在的文件：{target}")

    for rel in ("references/usage.md", "references/root-items.md",
                "references/safety.md", "scripts/standard.py"):
        if not (skill_dir / rel).exists():
            errors.append(f"缺关键资源：{rel}")

    return errors


def main() -> int:
    if not SKILLS.is_dir():
        print(f"FAIL 找不到 skills/：{SKILLS}")
        return 1
    found = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    if not found:
        print("FAIL skills/ 下没有技能目录")
        return 1

    bad = 0
    for skill_dir in found:
        errors = check_skill(skill_dir)
        if errors:
            bad += 1
            print(f"FAIL {skill_dir.name}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"ok   {skill_dir.name}")
    print()
    print(f"{'PASS' if bad == 0 else 'FAIL'} {len(found) - bad}/{len(found)} 个技能通过")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
