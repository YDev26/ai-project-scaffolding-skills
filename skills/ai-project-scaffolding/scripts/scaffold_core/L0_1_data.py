"""V1 根骨架的根项数据（从开发源裁剪的根段投影）。

为什么：
  数据与逻辑分开：三档、根项、隐藏项都只在这里定义，判档与闸共用
  数据只读：不在本文件落盘或解析路径，便于单独审阅与替换
  根段裁剪：开发源里的细段常量不进入 V1
真实流程：
  档位 → 可见根项；根项 → 默认隐藏项
概念：
  数据只读；不落盘、不解析模板路径
  尾斜杠表示目录项，文件项没有尾斜杠
  .git 不在这里创建：git init 是用户动作
跑：
  由 tier_pipeline 与 gate_pipeline 导入
入：
  无
出：
  STRUCT / ROOT_HIDDEN_FILES / ROOT_HIDDEN_DIRS
"""


STRUCT = {
    # 档位 → 可见根项；尾斜杠表示目录项，文件项没有尾斜杠。
    "小": ["README.md", "src/", "docs/"],
    "中": ["README.md", "AGENTS.md", "docs/", "src/", "tests/", "examples/"],
    "大": ["README.md", "AGENTS.md", "docs/", "src/", "tests/", "examples/",
           "LICENSE.txt", "pyproject.toml", "thirdparty/", "assets/"],
}

ROOT_HIDDEN_FILES = {
    # 隐藏文件 → 初始内容；只填 0 字节占位，已存在的非空文件不覆盖。
    ".gitignore": "__pycache__/\n*.py[cod]\n.venv/\n.env\n*.tmp\n",
    ".gitattributes": "* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n",
}

ROOT_HIDDEN_DIRS = [
    # 隐藏目录 → 缺失时创建，并在目录内补 .gitkeep 以便版本库保留空目录。
    ".github",
]
