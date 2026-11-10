# 兼容与验证状态

技能使用 Agent Skills 基础格式: 目录名 / SKILL.md 与 YAML frontmatter; 必填 name / description, 本仓另用 license / compatibility / metadata.

## 2026-11-10 本机证据

| 检查 | 当前证据 | 边界 |
|---|---|---|
| 结构 | 自有 validate_skill 通过; Agent Skills 参考校验器 skills-ref 通过; Claude plugin validate --strict 通过 | 不证明模型行为 |
| 回归 | 安装后运行 tests/run_tests.py --installed-cli, 22/22, exit 0 | Windows / Python 3.11 |
| 计划样例 | check_evals.py --run-plans: 12 正 / 12 负结构, 三档计划 3/3, 无目标写入, exit 0 | 结构与 CLI 执行, 不是真实模型触发率 |
| 独立技能 | 只复制技能目录到临时 .agents/skills, 从无仓根 README / pyproject 的目录运行 B 四步通过 | 不依赖完整开发仓 |
| 安装 CLI | 完整分发仓离线 wheel 构建, 干净 venv 安装 1.0.0, 从无关目录执行 C 查询 / 规划 / 创建 / 根闸通过 | 不代表其他平台已测 |
| 真实会话 | Claude Code 2.1.286: 中文规划请求自动选中技能; SQL 维护请求没有调用技能 | 2026-11-11 定向行为复测通过确认 / 取消 / 默认项 / 路径 / 细段边界 |

## 校验器差异

本机 skill-creator 的 quick_validate 拒绝现有 compatibility 字段(自身白名单不含该项), exit 1; 未为迁就该工具删除字段. 相同技能经 Agent Skills 参考校验器 skills-ref、完整 YAML 解析和本仓校验通过. quick_validate 最初因缺 PyYAML 不能启动, 补临时依赖后确认上述白名单差异; 这些辅助依赖未写入项目运行依赖.

## AI 客户端矩阵

| 客户端 | 结构 / 安装 | 真实触发与执行 |
|---|---|---|
| Claude Code 2.1.286 | manifest 与技能结构通过; 隔离 .claude/skills 被发现 | 2026-11-11 Read/Skill/PowerShell 的 B 模式确认后创建及根闸通过; Read/Skill 的 A 规划路径和默认项复测通过; C 模型执行未单独测(程序安装回归已测) |
| Codex | 本轮未安装或实测该技能 | 未测 |
| Hermes | 本轮未安装或实测该技能 | 未测 |
| Cursor / Gemini CLI / GitHub Copilot / OpenCode | 本轮未安装或实测该技能 | 未测 |

不把 Claude Code 客户端等同于 Claude 模型. 未进行 24 个请求的完整真实触发评测, 不提供总体准确率.

## 远端与待测

- 公开仓: https://github.com/YDev26/ai-project-scaffolding-skills.
- Linux / macOS、Python 3.10 / 3.12 未实测; GitHub CI 已配置 Windows/Linux × 3.10/3.12.
- 文件链接行为未实测.
- 2026-11-11 已完成指定技能的写入前确认 / 确认后创建 / 非空保留 / 取消 / A 默认项与目标 / 拒绝细段行为验收; 非完整 24 请求准确率或所有模型保证.
- GitHub 私密漏洞报告已启用(2026-11-10 经用户确认, 公开 API 返回 enabled=true).

## 可移植规则与位置

1. 不依赖 Claude 专用 hooks、context: fork、model 或 effort 扩展.
2. 运行脚本仅用 Python 标准库; V1 仅根骨架.
3. 执行说明和随包引用自足; 无 Python 或命令执行工具时可按 A 手工规划 / 创建, 必须声明“未跑闸”.
4. B/C 的程序闸通过只证明根结构; 只规划时不得写入.

```text
项目(Claude Code)    .claude/skills/ai-project-scaffolding/
项目(跨客户端)       .agents/skills/ai-project-scaffolding/
个人(Claude Code)    ~/.claude/skills/ai-project-scaffolding/
Hermes(Windows)      %LOCALAPPDATA%/hermes/skills/ai-project-scaffolding/
```
