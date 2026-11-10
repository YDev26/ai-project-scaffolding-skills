# 贡献说明

欢迎围绕 V1 根骨架范围提交问题和改进. 修改前按 AGENTS.md -> README.zh-CN.md -> 任务相关正文阅读.

## 本地验证

在完整分发仓根安装并运行:

```bash
python -m pip install .
python scripts/validate_skill.py
python scripts/check_evals.py --run-plans
python tests/run_tests.py --installed-cli ai-project-scaffold
python -m compileall -q skills
```

只验证源码时可运行 python tests/run_tests.py, 其中安装 CLI 用例会明确跳过; 不能把此结果当作安装验收完成.

## 修改约定

- SKILL.md 保持精简英文且少于 500 行; frontmatter name 与目录名一致, 保留 license 和 compatibility.
- AGENTS / SKILL 承担英文执行指令; 中文文档和注释解释目标、依据与限制; 路径、标识符及协议键用英文.
- Python 仅用标准库, 不引入网络、第三方运行依赖或上游动态导入.
- V1 只交付根骨架, 细骨架、细模板和细闸留待后续版本.
- 用户可见变化写入 CHANGELOG.md, 同步使用说明与必要反例.
- evals 的结构检查、CLI 计划验证、真实模型行为评测须分别记录; 不用程序检查结果替代真实模型结果.
