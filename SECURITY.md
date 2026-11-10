# 安全说明

## 支持状态

当前版本为 1.0.0, 维护 1.0.x 系列; 具体版本状态以发布记录为准.

## 问题报告

发现漏洞请私下联系维护者, 修复前不要在公开 issue 披露利用细节. 请使用 GitHub 的 [Private vulnerability reporting](https://github.com/YDev26/ai-project-scaffolding-skills/security/advisories/new). 维护者于 2026-11-10 确认已启用, 同日 GitHub 公开 API 返回 enabled=true; 无需公开个人邮箱. 提交报告时 GitHub 可能要求登录.

## 行为范围

- 入口为 skills/ai-project-scaffolding/scripts/standard.py 及同级四个包.
- 仅使用 Python 标准库; 无第三方运行依赖.
- 不联网、不下载模板、不访问凭据、不执行 git init.
- 只创建缺失根项并保留非空文件; 零字节隐藏配置可补默认值; 部分失败没有自动回滚.
- 从不可信来源安装前应审阅 SKILL.md 与 scripts/ 代码.

根闸通过只表示结构符合判据, 不代表安全审计或发布批准.
