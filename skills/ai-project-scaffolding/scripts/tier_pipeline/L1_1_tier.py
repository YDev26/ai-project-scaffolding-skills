"""V1 根骨架的判档逻辑（从开发源裁剪的根段投影）。

为什么：
  判档只做“命中即升、取最高”，规则在数据表，逻辑里不硬编码阈值
  默认小档：先给最小可用的根，再由触发升档，避免过度创建
  中档 + 公开触发用 LICENSE.txt 替 examples/：公开仓更需要许可证占位
真实流程：
  命中 ID 集合 → 校验 → 最高档胜出 → 可见根项
概念：
  默认小档；中档 + 公开触发时 LICENSE.txt 顶替 examples/
  switched 只表示发生了替换，展示文案由入口决定
跑：
  由 src/standard.py 的 tier 子命令导入
入：
  触发 ID 集合
出：
  (档位, 可见根项, switched)
"""
from tier_pipeline.L0_1_data import STRUCT, TRIGGERS, ORDER


def resolve(hits):
    """触发 ID 集合 → (档位, 可见根项, switched)。

    - 未知 ID 立即抛 ValueError，避免拼错后静默降到小档。
    - 命中即升、取最高；默认小档。
    - switched 只表示发生了「中档 + 公开」替换，展示文案由 CLI 决定。
    """
    ids = {h for h in hits}
    known = {t[0] for t in TRIGGERS}
    bad = ids - known
    if bad:
        raise ValueError(f"未知触发条件：{', '.join(sorted(bad))}（用 --list 看可用 id）")
    tier = "小"
    # ORDER 只用于比较：小 < 中 < 大；取命中里的最高档。
    for tid, _, target, _ in TRIGGERS:
        if tid in ids and ORDER[target] > ORDER[tier]:
            tier = target
    items = list(STRUCT[tier])
    switched = None
    if tier == "中" and "公开" in ids:
        # 公开项目用 LICENSE.txt 顶替 examples/；示例内容改放 docs/。
        items = ["LICENSE.txt" if x == "examples/" else x for x in items]
        switched = "中档 + 公开 ⇒ `LICENSE.txt` 顶替 `examples/`（示例并进 `docs/`）"
    return tier, items, switched
