> 本文档 `README.zh-CN.md` | 版本: v1 | 读者: 双方 | 作用: 中文真相源与导航 | 真相源: 本文件
# ai-project-scaffolding-skills | V1 根骨架

> 本文是中文真相源; 根 README 是英文展示副本, 冲突以本文为准.

## 1. 项目上下文

- 本仓面向 AI 稳定使用, 交付根骨架技能与必要执行工具. V1 流程为需求 -> 十二问判档 -> 精确目标与计划 -> 人确认 -> 创建根项 -> 根闸; 细骨架, 文档模板及细闸从 V2 开始.
- 默认小档, 命中条件升档并取最高; 只计已发生或三个月内必然发生的需求. 小 / 中 / 大分别为 3 / 6 / 10 个可见根项, 隐藏项上限 6; 上限不是必须填满的配额.
- 根闸只查根项, 槽位, 类型, 预算及根 Markdown 白名单, 不代表内容, 业务或发布质量合格.

## 2. 项目使用者

需要 Python 3.10+, 零运行依赖. 源码入口无需安装; 安装 `python -m pip install .` 后可用 `ai-project-scaffold`, 构建依赖 setuptools>=68 和 wheel. `pip install .` 只在含 pyproject.toml 的完整分发仓根使用; 从其他目录执行 `python -m pip install "<distribution-repo>"`. 只复制技能目录时直接用 B, 无需安装包.

```bash
python skills/ai-project-scaffolding/scripts/standard.py tier --list --json
python skills/ai-project-scaffolding/scripts/standard.py tier --trigger public --plan --root ../my-project
```

先展示计划并等待用户确认, 然后单独执行:

```bash
python skills/ai-project-scaffolding/scripts/standard.py tier --trigger public --apply --root ../my-project
python skills/ai-project-scaffolding/scripts/standard.py check-root --tier medium --root ../my-project --json
python skills/ai-project-scaffolding/scripts/standard.py human --root ../my-project
```

`human` 是人类交互路径; AI 用 `tier --plan/--apply` + `check-root` 的非交互参数.

公开仓库为 [YDev26/ai-project-scaffolding-skills](https://github.com/YDev26/ai-project-scaffolding-skills), 安装 URL 为 https://github.com/YDev26/ai-project-scaffolding-skills.git. 完整分发仓也可用 `npx skills add "<distribution-repo>" --skill ai-project-scaffolding` 安装, 或直接复制技能目录.

### 2.1 执行模式

| 模式 | 需要 | 完成证据 |
|---|---|---|
| A 手工降级 | 无 | 人工清单; 不跑根闸 |
| B 随技能脚本(推荐) | Python 3.10+ | `check-root` 退出码 0 |
| C 安装后 CLI | Python 3.10+ 且 `pip install .` | `check-root` 退出码 0 |

A 模式必须声明「未跑闸」; 上面的脚本示例为 B. C 安装后把脚本前缀替换为 ai-project-scaffold. 三模式均展示同一套可见项和默认隐藏项; 只规划时不写入.

- 容器目录未给项目名时先询问; 展示精确目标和完整计划后等待下一条确认回复, 目标或计划变化须重新确认. --plan 与 --apply 分开工具调用.
- 先确认计划再 --apply; 人工向导须输入 yes. --apply --dry --json 只预演, 不写目标. 非空文件不覆盖, 零字节 .gitignore / .gitattributes 会填默认值.
- 创建前检查非计划可见项与类型冲突, 已发现冲突不写入; 检查后的 IO 错误仍可能部分创建, 不提供事务回滚.
- 根段只建占位与默认隐藏配置, 采用者自行填写 README, AGENTS 和真实许可证正文.
- V1 工具运行不联网, 不拉模板.
- 安装后操作约定以随包[使用说明](skills/ai-project-scaffolding/references/usage.md)为定义源; 本文负责项目上下文与导航, 使用说明无需仓根 README 即可执行.
- AI 加载[英文技能](skills/ai-project-scaffolding/SKILL.md), 按其中自足流程执行; 需要理解判据或处理歧义时再查本文与[使用说明](skills/ai-project-scaffolding/references/usage.md), [根项速查](skills/ai-project-scaffolding/references/root-items.md), [安全边界](skills/ai-project-scaffolding/references/safety.md).

## 3. 项目开发者 / AI

### 3.1 读序: [英文 AGENTS](AGENTS.md) -> 本文 -> [文档索引](docs/INDEX_1.md) -> 任务相关正文.
AGENTS 规定工作边界, 本文提供上下文与导航, SKILL 给出采用者操作流程.

### 3.2 规范: 代码, 标识符, 路径和协议键使用英文.

读序不代表权威高低; 语言不决定权威.

AGENTS / SKILL 用精简英文承载执行约束; 真相源 README, 解释文档与代码注释使用中文, 便于审核目标, 依据, 取舍. 根英文 README 只展示.

不强制用户交流语言; AI 可按用户语言报告结果; 包括开发偏好语言也只是建议, 一切以用户为准.

### 3.3 导航: 功能核住 skills/ai-project-scaffolding/scripts/, tests/ 是验证辅助.

```bash
python scripts/check_evals.py --run-plans
python tests/run_tests.py --installed-cli ai-project-scaffold
```

安装 CLI 后运行第二条; 仅跑 python tests/run_tests.py 时, 安装专用用例会明确跳过. 兼容与真实模型证据见 COMPATIBILITY.md.

## 4. 协议
CLI 帮助, 提示, 错误和 JSON 默认英文, 档位 small / medium / large, 触发 ID 用 --list 查询; 中文别名仅为输入兼容. JSON 不再附带重复 _zh 字段, interface_version=3; 既有 tier / triggered / apply / pass 等主字段保持. 路径和原始系统错误按实际内容保留, 不能为了英文展示改写用户路径. 详细参数与退出码见[使用说明](skills/ai-project-scaffolding/references/usage.md).

## 5. 边界

技能独立运行, 不从上游动态加载代码; 上游保留细段供后续版本迭代.

执行任何会写入文件的程序前, 先获得采用者允许; 执行任何可能产生覆盖的操作前, 先询问是否已备份, 以及该操作是否可回滚.
