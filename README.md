# vtags-standalone

Verilog HDL 代码导航工具，独立于 Vim。支持模块拓扑、信号追踪、模块搜索等功能。

## 快速安装

```bash
tar -xzf vtags-standalone.tar.gz
cd vtags-standalone
./install.sh
```

安装脚本会：
1. 提示输入 vtags 安装路径（默认 `~/vtags`）
2. 复制 vtags 源码到目标路径
3. 编译 C Parser（需要 gcc）
4. 安装 OpenCode skill 到 `~/.config/opencode/skills/vtags-standalone/`

## 系统要求

- Python 3.6+
- GCC（用于编译 Parser）
- OpenCode（使用 skill 功能）

## 使用方法

安装完成后，在 OpenCode 中可以直接使用 vtags 功能：

```
帮我分析 switch_core_top 模块的拓扑结构
追踪 signal_x 信号的源头
搜索所有包含 mng 的模块
```

OpenCode 会自动加载 vtags-standalone skill 并执行相应命令。

## 命令行使用

```bash
# 列出顶层模块
python3 <vtags_path>/Standalone/cli.py -db ./vtags.db tops

# 查看模块拓扑
python3 <vtags_path>/Standalone/cli.py -db ./vtags.db topo <module> [depth]

# 查看模块信息
python3 <vtags_path>/Standalone/cli.py -db ./vtags.db info <module>

# 搜索模块
python3 <vtags_path>/Standalone/cli.py -db ./vtags.db search "*pattern*"

# 追踪信号源
python3 <vtags_path>/Standalone/cli.py -db ./vtags.db strace <signal> <file> <line>

# 追踪信号目的地
python3 <vtags_path>/Standalone/cli.py -db ./vtags.db dtrace <signal> <file> <line>
```

## 生成 vtags.db 数据库

```bash
# 进入项目目录
cd /path/to/verilog/project

# 创建文件列表
find . -name "*.v" > design.f

# 生成数据库
python3 <vtags_path>/vtags.py -f design.f
```

## 目录结构

```
vtags-standalone/
├── README.md          # 本文件
├── install.sh         # 安装脚本
├── skill/
│   └── SKILL.md       # OpenCode skill 定义
└── vtags/             # vtags 完整源码
    ├── Standalone/    # 独立命令行工具
    ├── Parser/        # C Parser
    ├── Lib/           # 核心库
    └── ...
```

## 更多信息

- vtags 原项目: https://github.com/user/vtags
- OpenCode 文档: https://opencode.ai/docs/skills/
