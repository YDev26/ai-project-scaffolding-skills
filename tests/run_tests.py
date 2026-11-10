#!/usr/bin/env python
"""V1 根骨架黑盒回归：临时目录隔离，只检验外部可观察的约定与失败边界。

测试通过子进程调用 skills/ai-project-scaffolding/scripts/standard.py，断言退出码、输出文本和 JSON 协议；
不 import 被测实现，也不依赖开发仓的细段模块。
"""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
INSTALLED_CLI = None


def skill_root():
    """技能目录；ROOT 可被 --root 覆盖，所以每次调用时计算。"""
    return ROOT / "skills" / "ai-project-scaffolding"


class ReleaseTests(unittest.TestCase):
    """黑盒回归：每个用例在独立临时目录里调用技能内 scripts/standard.py。"""

    def setUp(self):
        """建临时根目录，并注册退出时清理；target 是每次用例的目标项目。"""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.target = self.base / "project"

    def cli(self, *args, code=0, stdin=None):
        """跑一次技能内 scripts/standard.py，断言退出码并返回 stdout。

        - 清掉 PYTHONPATH：子进程只从当前技能仓导入，避免误用开发仓模块。
        - -B：不写 __pycache__，临时目录退出即干净。
        - UTF-8 + timeout：Windows 控制台默认 GBK，且防止挂起。
        """
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        env.pop("PYTHONPATH", None)
        result = subprocess.run([sys.executable, "-B", str(skill_root() / "scripts/standard.py"), *map(str, args)],
                                cwd=self.base, input=stdin, capture_output=True, text=True,
                                encoding="utf-8", env=env, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.stdout

    # 按触发条件在目标目录创建根项，返回 --apply 的 JSON 载荷。
    def create(self, *hits):
        """按触发 ID 创建根项，返回 --apply 的 JSON 载荷。"""
        flags = [flag for hit in hits for flag in ("--trigger", hit)]
        return json.loads(self.cli("tier", *flags, "--apply", "--root", self.target, "--json"))

    # 跑根闸并顺带校验协议：pass 与退出码一致、无未翻译诊断、无中文字符、无 _zh 字段。
    def gate(self, tier="small", code=0):
        """跑根闸，断言 pass / 退出码 / 文本纪律一致，并返回 JSON 载荷。"""
        payload = json.loads(self.cli("check-root", "--tier", tier, "--root", self.target, "--json", code=code))
        self.assertEqual(payload["pass"], code == 0)
        for message in payload["notes"] + payload["problems"]:
            self.assertNotIn("Root operation diagnostic", message)
            self.assertNotRegex(message, r"[\u4e00-\u9fff]")
        self.assert_no_translation_fields(payload)
        return payload

    # 正例：--list 十二问齐全且 ID 唯一；--plan 与 --dry 预演都不落盘。
    def test_container_and_unplanned_entries_fail_before_writing(self):
        """项目集合及计划外文件在计划/创建/预演阶段均拒绝, 既有树不变。"""
        self.target.mkdir()
        (self.target / "other-project").mkdir()
        (self.target / "other-project" / "data.txt").write_bytes(b"human content")
        (self.target / "notes.txt").write_bytes(b"keep")
        before = {p.relative_to(self.target): p.read_bytes() if p.is_file() else None
                  for p in self.target.rglob("*")}
        for flags in [("--plan",), ("--apply",), ("--apply", "--dry")]:
            result = json.loads(self.cli("tier", "--trigger", "build", *flags,
                                         "--root", self.target, "--json", code=1))
            report = result["plan" if "--plan" in flags else "apply"]
            self.assertEqual(len(report["errors"]), 2)
            self.assertTrue(all("Unplanned root entry:" in e for e in report["errors"]))
            if "apply" in result:
                self.assertEqual(report["created"], [])
            self.assertEqual(before, {p.relative_to(self.target): p.read_bytes() if p.is_file() else None
                                      for p in self.target.rglob("*")})

    def test_plan_does_not_allow_later_conflicts(self):
        """规划后目录变化, apply 必须重新检查且不创建其他根项。"""
        json.loads(self.cli("tier", "--plan", "--root", self.target, "--json"))
        self.target.mkdir()
        (self.target / "src").write_bytes(b"keep this file")
        result = json.loads(self.cli("tier", "--apply", "--root", self.target, "--json", code=1))
        self.assertEqual(result["apply"]["created"], [])
        self.assertIn("Type conflict:", result["apply"]["errors"][0])
        self.assertEqual(list(self.target.iterdir()), [self.target / "src"])
        self.assertEqual((self.target / "src").read_bytes(), b"keep this file")

    def test_existing_adapter_and_git_directory_remain_supported(self):
        """已知适配入口与隐藏 git 元数据不被误判为项目集合。"""
        self.target.mkdir()
        (self.target / "CLAUDE.md").write_bytes(b"adapter")
        (self.target / ".git").mkdir()
        self.create()
        self.gate()
        self.assertEqual((self.target / "CLAUDE.md").read_bytes(), b"adapter")

    def test_queries_and_plans_do_not_write(self):
        rows = json.loads(self.cli("tier", "--list", "--json"))
        self.assertEqual(len(rows), 12)
        self.assertEqual(len({row["id"] for row in rows}), 12)
        for command in (["--plan"], ["--apply", "--dry"]):
            result = json.loads(self.cli("tier", *command, "--root", self.target, "--json"))
            self.assertEqual(result["tier"], "small")
            self.assertFalse(self.target.exists())

    # 正例：零/一/二触发分别落小/中/大档，根项数与档位一致，创建后根闸通过，docs/ 与 src/ 保持空。
    def test_three_tiers_and_root_gate(self):
        for hits, tier, count in [((), "small", 3), (("collaboration",), "medium", 6), (("build",), "large", 10)]:
            with self.subTest(tier=tier):
                self.target = self.base / tier
                result = self.create(*hits)
                self.assertEqual(result["tier"], tier)
                self.assertEqual(len(result["visible"]), count)
                self.gate(tier)
                # 根段绝不把文档内部或代码内部结构铺进去。
                self.assertEqual(list((self.target / "docs").iterdir()), [])
                self.assertEqual(list((self.target / "src").iterdir()), [])

    # 正例+负例：公开触发换得 LICENSE.txt 替代 examples/；私建 examples/ 目录后根闸必须 FAIL。
    def test_public_medium_substitution(self):
        result = self.create("public")
        self.assertEqual(result["tier"], "medium")
        self.assertTrue((self.target / "LICENSE.txt").is_file())
        self.assertFalse((self.target / "examples").exists())
        self.gate("medium")
        (self.target / "examples").mkdir()
        self.gate("medium", code=1)

    # 正例：多触发并存取最高档（大），重复触发不改变结果。
    def test_highest_trigger_wins(self):
        result = self.create("public", "build", "collaboration", "build")
        self.assertEqual(result["tier"], "large")
        self.gate("large")

    # 正例：既有非空文件逐字节保留；重复创建 created 为空、整树快照不变（幂等）。
    def test_nonempty_preserved_and_repeat_idempotent(self):
        self.target.mkdir()
        for name in ["README.md", ".gitignore", ".gitattributes"]:
            (self.target / name).write_bytes(b"human content\r\n")
        self.create()
        snapshot = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        result = self.create()
        self.assertEqual(result["apply"]["created"], [])
        self.assertEqual(snapshot, {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()})
        for name in ["README.md", ".gitignore", ".gitattributes"]:
            self.assertEqual((self.target / name).read_bytes(), b"human content\r\n")

    # 正例：空的隐藏配置文件填充默认内容（无 CR），空的可见文件保持为空不擅写。
    def test_empty_hidden_configs_are_filled_but_visible_is_empty(self):
        self.target.mkdir()
        for name in ["README.md", ".gitignore", ".gitattributes"]:
            (self.target / name).touch()
        self.create()
        self.assertEqual((self.target / "README.md").stat().st_size, 0)
        for name in [".gitignore", ".gitattributes"]:
            data = (self.target / name).read_bytes()
            self.assertGreater(len(data), 0)
            self.assertNotIn(b"\r", data)

    # 负例：槽位类型被异类占据（文件位遇目录、目录位遇文件）报 Type conflict 且不覆盖既有内容。
    def test_wrong_types_fail_without_overwrite(self):
        for name in ["src", ".github", ".gitignore"]:
            with self.subTest(name=name):
                self.target = self.base / name.lstrip(".")
                self.target.mkdir()
                p = self.target / name
                p.mkdir() if name == ".gitignore" else p.write_text("keep", encoding="utf-8")
                result = json.loads(self.cli("tier", "--apply", "--root", self.target, "--json", code=1))
                self.assertTrue(result["apply"]["errors"])
                self.assertTrue(all(e.startswith("Type conflict:") for e in result["apply"]["errors"]))
                self.assertTrue(p.is_dir() if name == ".gitignore" else p.read_text() == "keep")

    # 负例：目标不存在时根闸 FAIL；目标是文件时创建 FAIL 且文件原样保留；事后根闸仍 FAIL。
    def test_target_file_and_missing_gate_fail(self):
        self.gate(code=1)
        self.target.write_text("keep", encoding="utf-8")
        self.cli("tier", "--apply", "--root", self.target, "--json", code=1)
        self.assertEqual(self.target.read_text(), "keep")
        self.gate(code=1)

    # 负例矩阵：缺根项/多根项/类型不符/隐藏预算超限/根 .md 白名单外，五类违规各自 FAIL 且出 problems。
    def test_gate_negative_boundaries(self):
        for mutation in ["missing", "extra", "type", "hidden", "markdown"]:
            with self.subTest(mutation=mutation):
                self.target = self.base / mutation
                self.create()
                if mutation == "missing":
                    (self.target / "README.md").unlink()
                elif mutation == "extra":
                    (self.target / "random.txt").touch()
                elif mutation == "type":
                    (self.target / "src").rmdir()
                    (self.target / "src").touch()
                elif mutation == "hidden":
                    for n in range(4):
                        (self.target / f".extra{n}").touch()
                else:
                    (self.target / "notes.md").touch()
                self.assertTrue(self.gate(code=1)["problems"])

    # 正例：大档槽位改名（构建锚点/依赖槽/自由槽各候选类型）后根闸仍通过；负例：多出的根项必须 FAIL。
    def test_large_slot_alternatives_and_duplicates(self):
        self.create("build")
        for old, new in [("pyproject.toml", "CMakeLists.txt"), ("thirdparty", "vendor"), ("assets", "public")]:
            (self.target / old).rename(self.target / new)
        self.gate("large")
        (self.target / "vendor").rmdir()
        (self.target / "DEPS").touch()
        self.gate("large")
        for extra, is_dir in [("Makefile", False), ("vendor", True), ("scripts", True)]:
            p = self.target / extra
            p.mkdir() if is_dir else p.touch()
            self.gate("large", code=1)
            p.rmdir() if is_dir else p.unlink()

    # 负例：detail 子命令、V2 旗标、未知触发、非法组合等一律退出 2 且不落盘。
    def test_cli_rejects_invalid_and_v2_flags(self):
        for args in [("check-detail",), ("tier", "--detail-apply"), ("tier", "--trigger", "unknown"),
                     ("tier", "--dry"), ("tier", "--plan", "--apply"), ("tier", "--list", "--root", str(self.target)),
                     ("check-root",), ("check-root", "--tier", "unknown")]:
            with self.subTest(args=args):
                self.cli(*args, code=2)
        self.assertFalse(self.target.exists())

    # 负例：向导拒绝确认（no）或 EOF 中断均不创建目标目录。
    def test_human_confirmation_cancel(self):
        self.cli("human", "--root", self.target, stdin="n\n" * 12 + "no\n")
        self.assertFalse(self.target.exists())
        self.cli("human", "--root", self.target, stdin="n\n", code=2)
        self.assertFalse(self.target.exists())

    # 正例：向导十二问全 no + yes 确认后创建最小根项并自动通过根闸。
    def test_human_confirm_and_gate(self):
        self.cli("human", "--root", self.target, stdin="n\n" * 12 + "yes\n")
        self.gate()

    # 正例：技能内 scripts 无 detail 命名/导入；版本为 1.0.0。
    def test_skill_scripts_no_detail_imports(self):
        scripts = sorted((skill_root() / "scripts").rglob("*.py"))
        self.assertTrue(scripts, "技能内没有 Python 代码")
        for p in scripts:
            tree = ast.parse(p.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    self.assertNotIn("detail", node.name.lower())
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn("detail", (node.module or "").lower())
        self.assertEqual(self.cli("--version").strip(), "1.0.0")

    def assert_no_translation_fields(self, payload):
        """协议不重复发出同一信息的中文副本。"""
        if isinstance(payload, dict):
            self.assertFalse(any(key.endswith("_zh") for key in payload))
            for value in payload.values():
                self.assert_no_translation_fields(value)
        elif isinstance(payload, list):
            for value in payload:
                self.assert_no_translation_fields(value)

    # 正例：协议字段纯 ASCII 且无 _zh 副本；中文触发别名与英文结果完全等价；中英档位别名都被根闸接受。
    def test_english_protocol_and_chinese_aliases(self):
        aliases = dict(zip(
            ["collaboration", "test-suite", "external-examples", "many-docs", "public", "multiple-entrypoints",
             "shipped-assets", "build", "layering", "over-12-docs", "ci", "firmware-and-host"],
            ["协作", "用例多", "外部示例", "文档多", "公开", "多入口", "资产", "构建", "分层", "文档超12", "CI", "硬软双栈"]))
        rows = json.loads(self.cli("tier", "--list", "--json"))
        self.assert_no_translation_fields(rows)
        self.assertEqual({row["id"] for row in rows}, set(aliases))
        for row in rows:
            with self.subTest(trigger=row["id"]):
                self.assertTrue(row["id"].isascii())
                self.assertTrue(row["ask"].isascii())
                self.assertTrue(row["why"].isascii())
                english = json.loads(self.cli("tier", "--trigger", row["id"], "--json"))
                chinese = json.loads(self.cli("tier", "--trigger", aliases[row["id"]], "--json"))
                self.assertEqual(english, chinese)
                self.assert_no_translation_fields(english)
                self.assertEqual(english["tier"], row["upgrade_to"])
                self.assertIn(english["tier"], ["small", "medium", "large"])
                self.assertEqual(english["triggered"][0]["id"], row["id"])
        result = self.create("public")
        self.assert_no_translation_fields(result)
        self.assertTrue(result["substitution"].isascii())
        self.gate("medium")
        self.gate("中")

    # 正例：--help、计划输出与向导交互显示全部无中文字符；取消路径文案符合约定。
    def test_english_help_and_human_display(self):
        for args in [("--help",), ("tier", "--help"), ("check-root", "--help"), ("human", "--help")]:
            output = self.cli(*args)
            self.assertRegex(output, r"(?i)usage")
            self.assertNotRegex(output, r"[\u4e00-\u9fff]")
        output = self.cli("tier", "--plan", "--trigger", "public", "--root", self.target)
        self.assertTrue(output.startswith("Tier: medium;"))
        self.assertNotRegex(output, r"[\u4e00-\u9fff]")
        # 十二问全答 n，再回答确认（no）；确认前不应写任何文件。
        output = self.cli("human", "--root", self.target, stdin="n\n" * 12 + "no\n")
        self.assertIn("Confirm creation? Type yes:", output)
        self.assertIn("Cancelled; nothing written", output)
        self.assertNotRegex(output, r"[\u4e00-\u9fff]")
        self.assertFalse(self.target.exists())

    # 正例：AGENTS/SKILL 执行入口纯英文且指向中文真相源。
    def test_execution_entries_and_chinese_truth(self):
        for rel in ["AGENTS.md", "skills/ai-project-scaffolding/SKILL.md"]:
            content = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotRegex(content, r"[\u4e00-\u9fff]", rel)
            self.assertIn("README.zh-CN.md", content)
        content = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("中文真相源", content)
        self.assertIn("语言不决定权威", content)

    def test_documented_commands_with_detached_skill(self):
        """只复制技能目录, 在无仓根文件的采用者目录执行说明中的 B 命令。"""
        detached = self.base / ".agents" / "skills" / "ai-project-scaffolding"
        shutil.copytree(skill_root(), detached, ignore=shutil.ignore_patterns("__pycache__"))
        self.assertFalse((self.base / "README.zh-CN.md").exists())
        self.assertFalse((detached / "pyproject.toml").exists())
        # 技能内的可点引用在独立安装后仍应存在, 不向外读取仓根 truth。
        for document in [detached / "SKILL.md", *sorted((detached / "references").glob("*.md"))]:
            for url in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                path = url.split("#")[0]
                if path and "://" not in path:
                    resolved = (document.parent / path).resolve()
                    self.assertTrue(resolved.is_relative_to(detached.resolve()), url)
                    self.assertTrue(resolved.exists(), url)
        usage = (detached / "references" / "usage.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```bash\n(.*?)```", usage, flags=re.S)
        commands = [line for block in blocks for line in block.splitlines()
                    if line.startswith('python "<skill-dir>/scripts/standard.py" ')]
        self.assertEqual(len(commands), 4, "缺独立技能查询 / 规划 / 创建 / 根闸示例")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        env.pop("PYTHONPATH", None)
        payloads = []
        for index, command in enumerate(commands):
            args = shlex.split(command)
            args = [arg.replace("<skill-dir>", detached.as_posix())
                    .replace("<target>", self.target.as_posix()) for arg in args[1:]]
            result = subprocess.run([sys.executable, "-B", *args], cwd=self.base,
                                    capture_output=True, text=True, encoding="utf-8",
                                    env=env, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payloads.append(json.loads(result.stdout))
            if index < 2:
                self.assertFalse(self.target.exists(), "查询 / 规划不得落盘")
        self.assertEqual(len(payloads[0]), 12)
        self.assertEqual(payloads[1]["tier"], "medium")
        self.assertFalse(payloads[2]["apply"]["errors"])
        self.assertTrue(payloads[3]["pass"])

    def test_installed_cli_from_unrelated_cwd(self):
        """显式指定已安装 CLI 时, 从无源码的目录执行文档中的 C 模式四步。"""
        if INSTALLED_CLI is None:
            self.skipTest("用 --installed-cli 指定已安装的 CLI; CI 必跑")
        usage = (skill_root() / "references/usage.md").read_text(encoding="utf-8")
        commands = [line for block in re.findall(r"```bash\n(.*?)```", usage, re.S)
                    for line in block.splitlines() if line.startswith("ai-project-scaffold ")]
        self.assertEqual(len(commands), 4)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        env.pop("PYTHONPATH", None)
        payloads = []
        for index, command in enumerate(commands):
            args = [str(self.target) if arg == "<target>" else arg for arg in shlex.split(command)[1:]]
            result = subprocess.run([str(INSTALLED_CLI), *args], cwd=self.base, env=env,
                                    capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payloads.append(json.loads(result.stdout))
            if index < 2:
                self.assertFalse(self.target.exists())
        self.assertEqual(len(payloads[0]), 12)
        self.assertEqual(payloads[1]["tier"], "medium")
        self.assertFalse(payloads[2]["apply"]["errors"])
        self.assertTrue(payloads[3]["pass"])

    def test_validation_hint_runs_without_cli_install(self):
        """照抄脚本的非 JSON 验收提示, 不依赖 PATH 中已安装的 console script。"""
        self.create()
        output = self.cli("tier", "--root", self.target)
        hint = next(line.removeprefix("Validate: ") for line in output.splitlines() if line.startswith("Validate: "))
        args = shlex.split(hint)
        self.assertEqual(Path(args[1]).resolve(), (skill_root() / "scripts/standard.py").resolve())
        result = subprocess.run([sys.executable, "-B", *args[1:]], cwd=self.base,
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Root validation passed", result.stdout)

    def test_plan_evals_and_invalid_contracts(self):
        """计划样例实跑; 畸形 JSON、错误类型及计划要求落盘文件均应失败。"""
        checker = ROOT / "scripts/check_evals.py"
        def run(*args):
            return subprocess.run([sys.executable, "-B", str(checker), *map(str, args)], cwd=self.base,
                                  capture_output=True, text=True, encoding="utf-8", timeout=30)
        result = run("--run-plans")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        source = json.loads((skill_root() / "evals/evals.json").read_text(encoding="utf-8"))
        legacy = json.loads(json.dumps(source))
        legacy["functional"][0]["expect_files"] = legacy["functional"][0].pop("expect_visible")
        malformed = self.base / "bad-evals.json"
        for value in [[], {"trigger": []}, legacy, {**source, "functional": [None, None, None]}]:
            malformed.write_text(json.dumps(value), encoding="utf-8")
            result = run("--evals", malformed, "--run-plans")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        wrong = json.loads(json.dumps(source))
        wrong["functional"][0]["expect_visible"] = ["WRONG"]
        malformed.write_text(json.dumps(wrong), encoding="utf-8")
        self.assertEqual(run("--evals", malformed, "--run-plans").returncode, 1)

    # 正例：发布文档内的相对链接全部指向存在的文件。
    def test_document_links_resolve(self):
        for rel in ["README.md", "AGENTS.md", "README.zh-CN.md", "docs/INDEX_1.md",
                    "skills/ai-project-scaffolding/references/usage.md",
                    "skills/ai-project-scaffolding/references/root-items.md",
                    "skills/ai-project-scaffolding/references/safety.md",
                    "skills/ai-project-scaffolding/SKILL.md"]:
            p = ROOT / rel
            for url in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
                path = url.split("#")[0]
                if path and "://" not in path:
                    self.assertTrue((p.parent / path).exists(), f"{rel}: {url}")


def main():
    """测试入口：--root 可指向技能仓根复跑同一套黑盒用例；失败退出 1。"""
    global ROOT, INSTALLED_CLI
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--installed-cli", help="Installed CLI path or name; runs required installation workflow")
    args = parser.parse_args()
    ROOT = args.root.resolve()
    if args.installed_cli:
        resolved = shutil.which(args.installed_cli)
        if not resolved:
            parser.error("--installed-cli does not resolve to an executable")
        INSTALLED_CLI = Path(resolved).resolve()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
