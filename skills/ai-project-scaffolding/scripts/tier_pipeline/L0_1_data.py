"""V1 根骨架的判档数据表（从开发源裁剪的根段投影）。

为什么：
  判档规则只写一份数据表，判定与展示都从这里读，避免调用处散落数字
  根段裁剪：只保留 V1 需要的触发与槽位，细段规则留在开发源
  数据只读：改阈值必须改这里，不在逻辑里硬编码
真实流程：
  命中触发条件 → 档位 → 可见根项 / 槽位候选
概念：
  小 3 / 中 6 / 大 10 个可见根项；隐藏项上限 6
  命中即升、取最高；默认小档
  TRIGGERS 每行 = (中文 ID, 人类问句, 升到哪档, 升级理由)
  大档三个槽位各取一个：构建锚点（文件）/ 依赖槽（默认目录，DEPS 是文件）/ 自由槽（目录）
  ROOT_HIDDEN_* 从 scaffold_core re-export，保持与开发源相同的导入面
跑：
  由 L1_1_tier.resolve 与根闸适配器导入
入：
  无
出：
  CAP / HIDDEN_CAP / BUILD_ANCHORS / DEP_SLOTS / DEP_FILE_SLOTS / FREE_SLOT / FREE_SLOT_KEY / TRIGGERS / ORDER
"""
from scaffold_core.L0_1_data import ROOT_HIDDEN_DIRS, ROOT_HIDDEN_FILES, STRUCT


CAP = {tier: len(items) for tier, items in STRUCT.items()}

HIDDEN_CAP = 6

BUILD_ANCHORS = {
    # 大档构建锚点候选：必须恰好一个，且必须是文件（不能是目录）。
    "CMakeLists.txt", "pyproject.toml", "Makefile", "configure",
    "Cargo.toml", "package.json", "SConstruct", "BUILD.bazel", "meson.build"}

DEP_SLOTS = {"thirdparty/", "third_party/", "vendor/", "deps/", "extern/", "external/", "DEPS"}

DEP_FILE_SLOTS = {"DEPS"}

FREE_SLOT = {
    # 大档自由槽候选：必须恰好一个，且必须是目录；键是判据，值是给人看的说明。
    "assets/": "内容型项目：图片/字体/模型/样例数据要**随包发布**（本项目根的填法；web 放 public/、应用放 src/resources/）",
    "scripts/": "构建/部署/打包脚本成套（Setup.bat / Release.py 一类）",
    "public/": "站点/前端的静态资源根（GitHub Pages、静态站）",
}

FREE_SLOT_KEY = "assets/"

TRIGGERS = [
    # 十二问：每行 = (中文 ID, 人类问句, 升到哪档, 升级理由)；命中即升，取最高。
    ("协作",   "会有第二个人读/改这个仓库吗（不含 AI）？",            "中", "契约要能独立传阅 ⇒ AGENTS.md 单列"),
    ("用例多", "回归用例会超过 3 条，或需要独立跑回归集吗？",          "中", "tests/ 独立成目录才跑得清"),
    ("外部示例", "要给仓库外的人拷/演示实物吗？",                      "中", "examples/ 独立存在，别塞 docs"),
    ("文档多", "除 README 外会有 4 份以上正文文档吗？",                "中", "docs/ 需要索引与分类"),
    ("公开",   "仓库要公开（GitHub 等）吗？",                          "中", "需要 LICENSE 与治理文件"),
    ("多入口", "会有第二个可执行入口或 5 个以上子命令吗？",            "中", "README 装不下两套用法"),
    ("资产",   "资产要**随包发布**吗（图片/字体/模型/样例数据，不是仓库里备用）？", "大", "要发布 ⇒ 要构建锚点与产物位；资产可放 assets/ 或 src/ 子层（落位自由）"),
    ("构建",   "需要编译/打包/出发布产物吗？",                        "大", "根要放构建锚点（CMake/pyproject）"),
    ("分层",   "代码会超 2000 行，或要适配 2 个以上平台吗？",          "大", "src/ 需要 adapters/modules/contract 三层"),
    ("文档超12", "正文文档会超过 12 份吗？",                           "大", "docs/ 需要子目录分类"),
    ("CI",     "要上 CI / 发布流水线（远程仓 + 自动跑）吗？",          "大", "需要 .github/workflows 与发布脚本"),
    ("硬软双栈", "有固件 + 上位机两个产物吗（嵌入式）？",              "大", "双产物 ⇒ 构建锚点必须占根、src/ 必分层；资产仍走自由槽"),
]

ORDER = {"小": 0, "中": 1, "大": 2}
