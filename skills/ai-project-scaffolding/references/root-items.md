> 本文档 `skills/ai-project-scaffolding/references/root-items.md` | 版本: v1 | 读者: AI 与人 | 作用: 三档根项, 十二触发, 三槽与根闸速查 | 真相源: 同目录 usage.md(操作约定); 仓根 README 仅提供项目上下文
# 根项速查

## 档位

| 档位 | 可见根项 |
|---|---|
| small | README.md, src/, docs/ |
| medium | README.md, AGENTS.md, docs/, src/, tests/, examples/; public 时 LICENSE.txt 替 examples/ |
| large | README.md, AGENTS.md, docs/, src/, tests/, examples/, LICENSE.txt, 构建锚点, 依赖槽, 自由槽 |

默认 small; 命中触发条件就升档, 多个命中取最高. 只计当前或三个月内必然发生的需求, 不计“以后可能”.

## 十二触发

| ID | 中文别名 | 问题 | 升到 |
|---|---|---|---|
| collaboration | 协作 | 是否有第二个人读改仓库(不含 AI) | medium |
| test-suite | 用例多 | 回归是否超过三条, 或需独立回归集 | medium |
| external-examples | 外部示例 | 是否给仓外的人复制或演示实物 | medium |
| many-docs | 文档多 | README 外正文是否至少四份 | medium |
| public | 公开 | 仓库是否公开 | medium |
| multiple-entrypoints | 多入口 | 是否有第二个可执行入口或至少五个子命令 | medium |
| shipped-assets | 资产 | 资产是否随产品发布 | large |
| build | 构建 | 是否编译, 打包或出发布产物 | large |
| layering | 分层 | 代码是否超过 2000 行, 或适配至少两个平台 | large |
| over-12-docs | 文档超12 | 正文是否超过十二份 | large |
| ci | CI | 是否运行远程 CI 或发布流水线 | large |
| firmware-and-host | 硬软双栈 | 是否交付固件和上位机两个产物 | large |

## 大档三槽

每槽恰好一项, 可采用不同名称:

- 构建锚点(文件): CMakeLists.txt, pyproject.toml, Makefile, configure, Cargo.toml, package.json, SConstruct, BUILD.bazel, meson.build.
- 依赖槽(目录, DEPS 除外): thirdparty/, third_party/, vendor/, deps/, extern/, external/, DEPS(文件).
- 自由槽(目录): assets/, scripts/, public/.

生成器固定使用 pyproject.toml, thirdparty/, assets/; CLI 没有槽位改名参数. 要用替代项, 先让用户确认手工方案, 用 A 创建或让用户批准生成后的调整; 不能只改口头计划却用 B/C 声称已生成替代项, 也不能叠加多个候选.

## 隐藏预算与根闸

- A/B/C 默认隐藏项相同: .gitignore, .gitattributes, .github/. 是否公开或使用 CI 不改变这些默认项; 需求另有约定时先明确偏差.
- 隐藏上限 6, .git 计入; 虚拟环境 / 编辑器缓存等机器产物豁免, 精确列表见根闸常量.
- CLAUDE.md 是可选适配入口: 根层允许, 不占可见项, 不自动创建.
- 根闸只查根项与档位, 三槽数量和类型, 隐藏预算, 根 Markdown 白名单.
- 根闸不检查文档内容, 业务代码, 示例质量或发布资格.

## A 模式手工清单

1. 容器目录缺项目名先问, 不复用旧名称; 目标或计划变化须重新确认. 先确认用户目标的绝对路径(有子目录名时保留它), 再回答十二问, 展示目标、档位、可见根项及三个默认隐藏项, 等待用户下一条回复确认后才单独创建. 只规划的请求停在此处, 不写入.
2. 获授权后仅建缺失项: 目录用 mkdir, 可见文件建零字节占位; 不填 README / AGENTS / 许可证正文.
3. 隐藏配置默认内容见 scripts/scaffold_core/L0_1_data.py; 只新建或填零字节配置, 非空不覆盖. .github/ 缺失时建目录及 .gitkeep; 不创建 .git.
4. 报告手工核对结果并声明“未跑闸”, 不能声称根闸通过.
