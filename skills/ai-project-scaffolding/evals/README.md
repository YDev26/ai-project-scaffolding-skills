# 评测说明

`evals.json` 分三组:

- trigger.should_trigger: 12 条应触发请求, 包含英文与中文.
- trigger.should_not_trigger: 12 条不应触发的近似请求, 包含维护现有仓库和细骨架越界请求.
- functional: small / medium-public / large 三个 CLI 计划样例.

在完整分发仓运行:

```bash
python scripts/check_evals.py
python scripts/check_evals.py --run-plans
```

第一条只查结构. 第二条在隔离临时目录中为每例注入 --root, 比对 JSON 的 tier / visible 与 expect_tier / expect_visible, 并确认目标不存在. --plan 不写文件, 所以不使用 expect_files. 创建与安装后的完整流程由 tests/run_tests.py 验证:

```bash
python tests/run_tests.py --installed-cli ai-project-scaffold
```

这些是程序验证, 不证明模型选技能或按技能行动. 真实模型评测应逐例启动新会话, 记录 AI 客户端 / 后端模型 / 工具权限、是否加载技能、十二问依据、写入确认、越界行为和实际产物. 应触发与不应触发请求分别计数, 不以同一会话背答案的自评分替代. 只装技能、无 shell 的环境可测 A, 不能宣称 B/C 已通过.

此文件属于随技能分发的说明, 独立安装时无需访问仓根记录.

定向行为复验已覆盖确认前不写、确认后创建及保留内容、默认项与目标路径、取消和细段越界; 本机基本可用, 不把该定向验收当成完整触发率或多平台保证. 超时驱动需检查 init 的实际工具名, 同时记录进度及总时长 / 空闲截止; 不记录推理正文或凭据.

## 目标与确认行为场景

以下供真实 AI 复测，不属于 --run-plans 的程序通过项。

| 输入 / 场景 | 应观察的结果 |
|---|---|
| 上轮确认 workspace/mc-like，本轮只说 create to 一个已有其他项目的父目录 | 只问项目目录名；不猜 mc-like，不调用创建 |
| 用户补充新目录名或换父目录 | 展示新绝对目标、完整可见 / 隐藏项及默认项，等待下一条用户确认 |
| 用户只要求计划，或旧确认后计划发生变化 | 不写入；变更后重新确认 |
| 用户确认当前精确计划 | 单独调用创建，再用同一路径跑根闸 |
| 规划后目标新增非计划项或 src 被文件占用 | CLI 退出 1，created 为空，原内容不变 |

程序回归只证明最后一类冲突会被检查，不能证明模型一定先询问或一定遵守确认时序。
