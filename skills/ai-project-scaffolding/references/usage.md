> 本文档 `skills/ai-project-scaffolding/references/usage.md` | 版本: v1 | 读者: 双方 | 作用: 判档, 参数, 退出码与写入边界说明 | 真相源: 本文(随技能分发的操作约定; 根 README.zh-CN.md 负责项目上下文)
# V1 使用说明

## 目标路径与确认

- 用户只给已有内容的父目录 / 项目集合目录而没给项目目录名时, 先问名称, 不复用上次名称, 不规划猜出的子目录, 不创建. 路径指项目本身还是父容器不明确时先问; 明确指定的既有项目可在检查与确认后补缺.
- 展示精确绝对目标、档位、完整可见 / 隐藏项、既有冲突和默认配置后, 等待用户下一条确认回复再写入. 父路径、子目录名、档位或根项清单改变, 均须重新展示并确认; 旧目标的 do it 与关闭工具审批均不替代确认.
- --plan 与 --apply 分开工具调用, 中间必须展示计划并收到用户确认, 不能放在同一批调用或同一轮连续执行. 创建与根闸沿用确认路径; 写入前再检查目录项, 发现计划后发生变化则停下更新计划并重新确认.
- V1 CLI 计划 / 创建前检查非计划可见项与类型冲突, 发现问题退出 1; 创建前发现的冲突不写任何根项. 检查无法判断人是否确认、也无法阻止 AI 在空父目录下猜出新名称; 对话确认仍由技能执行者负责. 检查后发生的权限 / IO 错误仍可能留下部分创建, 无事务回滚.
- 生成器固定使用默认槽名, 没有槽位改名参数. pyproject.toml 是空构建占位, .gitignore 默认含 Python 模式, 不表示项目已选 Python; 确认前须说明. 非 Python 项目如需其他构建锚点, 先确认手工方案, 不同时生成两个锚点, 不声称脚本已自动替换.


## 路径与操作依据

本文定义采用者的操作约定, 与 scripts/ 一同分发; root-items 和 safety 为速查摘要, 有歧义以本文为准. 完整仓根 README.zh-CN.md 负责项目背景与导航, 只安装技能目录也能执行, 不要求去采用者项目查找同名 README.

`<skill-dir>` 是包含 SKILL.md 的技能绝对目录; `<distribution-repo>` 是包含 pyproject.toml 的完整分发仓绝对目录; `<target>` 是采用者项目绝对目录. 三者不同, 不从当前工作目录猜测. 所有模式都须先把用户指定目标解析为绝对路径并写进计划; “当前目录下的 adopter”应为 <cwd>/adopter, 不能省掉子目录或改成技能安装目录. 确认、创建、根闸沿用同一目标.

## 执行模式

- **A 手工降级**: 无 Python; 按 [root-items](root-items.md) 手工建根项; 不跑根闸, 必须声明「未跑闸」.
- **B 随技能脚本**: Python 3.10+; `scripts/standard.py tier --plan/--apply` + `check-root`; 退出码 0 是完成证据.
- **C 安装后 CLI**: 在选定 Python 环境执行 `python -m pip install "<distribution-repo>"`, 再从同一环境调用 `ai-project-scaffold`; 与 B 同能力, 只是安装方式不同. 也可在完整分发仓根执行 `python -m pip install .`. 只复制的技能目录没有 pyproject.toml, 不在该目录安装, 使用 B 即可.
- 写入边界见 [safety](safety.md); 模式选择与五步流程见 SKILL.md.

## 判档与根项

B 通过 `python "<skill-dir>/scripts/standard.py" tier --list --json`, C 通过 `ai-project-scaffold tier --list --json` 获取十二问; 逐项答是 / 否与依据, 只计算已发生或三个月内必然发生的需求. 默认 small, 命中更高档就升级; AI 展示完整计划后取得人确认, 再创建.

| 档位 | 可见根项 |
|---|---|
| small(小) | README.md, src/, docs/ |
| medium(中) | README.md, AGENTS.md, docs/, src/, tests/, examples/; 公开时 LICENSE.txt 替 examples/ |
| large(大) | README.md, AGENTS.md, docs/, src/, tests/, examples/, LICENSE.txt, 构建锚点, 依赖槽, 自由槽 |

大档默认三槽为 pyproject.toml, thirdparty/, assets/. 根闸另接受构建锚点 CMakeLists.txt / Makefile / configure / Cargo.toml / package.json / SConstruct / BUILD.bazel / meson.build; 依赖槽 third_party/ / vendor/ / deps/ / extern/ / external/ / DEPS(DEPS 是文件); 自由槽 scripts/ / public/. 每槽恰好一个; 生成器固定使用默认名, CLI 没有槽位改名参数; 替代项须先由人确认手工方案, 用 A 创建或获准后调整已生成项, 不能只改口头计划却声称 B/C 已按替代项创建, 也不能叠加候选.

A/B/C 默认隐藏项相同: .gitignore, .gitattributes, .github/, 不因不公开或不用 CI 而自行删减, 不自动 git init. 隐藏上限 6, .git 也计入; 虚拟环境和编辑器等机器产物豁免, 具体清单见根闸常量. CLAUDE.md 是允许的可选根适配入口, 不占可见项, 不自动创建.

## 英文执行接口

稳定命令: tier, check-root, human, --version. human 是人类交互路径; AI 用 tier / check-root 的非交互参数. tier 参数为 --trigger(可重复), --list, --json, --plan, --apply, --root, --dry / --dry-run; --plan 与 --apply 互斥, --dry 必须配 --apply, --list 可单独使用; 与其他参数组合时只允许 --json. check-root 使用 --tier, --root, --json. 查询, 规划, 预演, 根闸不写目标; 未给 --root 时使用当前目录, 跨目录调用宜显式指定.

| 公开触发 ID | 中文输入别名 | 判断的问题 |
|---|---|---|
| collaboration | 协作 | 是否有第二个人读改(不含 AI) |
| test-suite | 用例多 | 回归超过三条, 或需独立回归集 |
| external-examples | 外部示例 | 是否给仓外的人复制或演示实物 |
| many-docs | 文档多 | README 外正文至少四份 |
| public | 公开 | 是否公开仓库 |
| multiple-entrypoints | 多入口 | 第二个可执行入口, 或至少五个子命令 |
| shipped-assets | 资产 | 资产是否随包发布 |
| build | 构建 | 是否编译, 打包或出发布产物 |
| layering | 分层 | 代码超过 2000 行, 或适配至少两个平台 |
| over-12-docs | 文档超12 | 正文是否超过十二份 |
| ci | CI | 是否上远程 CI / 发布流水线 |
| firmware-and-host | 硬软双栈 | 是否交付固件和上位机两个产物 |

--tier 主值为 small / medium / large, 仍接受小 / 中 / 大别名. 无论输入语言如何, JSON 主值始终英文; --list 的 ask / why 直接返回英文, 判据中文解释见本表. JSON 不附带重复 _zh 说明字段, interface_version=3; 不提供第二份默认机器译文, 也不因国际化翻译键与路径.

退出码 0 成功; 1 创建 / 根闸 / 文件系统失败; 2 参数错误或人工输入中断. JSON 文件系统异常返回 error=filesystem_error, message 和原始系统 detail; 参数错误由 argparse 输出到 stderr. pass 仅表示根闸结果, notes / problems 是诊断. 源报告遇到未知消息模板会保留原文, 防止诊断丢失.

## 写入边界与验收

- 创建缺失项, 不覆盖非空文件; 零字节隐藏配置可填默认值. 创建前已发现的根项冲突不写入; 检查后的 IO 错误可能部分创建, 无事务回滚. 根段不填 README / AGENTS / 许可证正文, 也不铺 docs 内部; 中档公开的 LICENSE.txt 为空占位, 不能当成合法发布许可. 采用者填内容后仍需业务与发布审查.
- 执行任何会写入文件的程序前, 先获得采用者允许; 执行任何可能产生覆盖的操作前, 先询问是否已备份, 以及该操作是否可回滚.
- 完整分发仓开发者在仓根执行 `python tests/run_tests.py`; 仅安装技能目录的采用者不依赖仓根测试文件. B/C 创建后按以下命令运行采用者根闸.

## 从任意工作目录调用

B: 替换绝对路径后执行, 查询和计划不写目标; 展示计划并获用户确认后才执行 --apply.

```bash
python "<skill-dir>/scripts/standard.py" tier --list --json
python "<skill-dir>/scripts/standard.py" tier --trigger public --plan --root "<target>" --json
```

展示上述计划, 等待用户确认后单独执行:

```bash
python "<skill-dir>/scripts/standard.py" tier --trigger public --apply --root "<target>" --json
python "<skill-dir>/scripts/standard.py" check-root --tier medium --root "<target>" --json
```

C: 先从完整分发仓安装并激活对应环境; 同样在确认计划后才创建.

```bash
ai-project-scaffold tier --list --json
ai-project-scaffold tier --trigger public --plan --root "<target>" --json
```

展示上述计划, 等待用户确认后单独执行:

```bash
ai-project-scaffold tier --trigger public --apply --root "<target>" --json
ai-project-scaffold check-root --tier medium --root "<target>" --json
```
