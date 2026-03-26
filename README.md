# openTrace-skill

Verilog HDL 代码导航工具。支持模块拓扑、模块追踪、信号追踪、模块搜索、VCD 波形分析等功能。

## 功能特性

### 核心能力

| 功能 | 说明 |
|------|------|
| 信号追踪 | `strace`/`dtrace` 精确定位信号源和目的地，10秒内完成问题定位 |
| 模块拓扑 | `topo` 展示模块层次结构，`info` 提供完整的 IO、参数、实例列表 |
| 搜索功能 | `search` 支持通配符，快速定位相关模块 |
| JSON 输出 | `-j` 参数输出结构化数据，便于程序化处理和自动化集成 |
| 独立运行 | 无需 Vim 环境，命令行直接使用，适合集成到其他工具和脚本 |

### 高级功能

- **递归追踪**：自动追踪信号完整传播链，支持跨模块追踪
- **VCD 波形分析**：结合波形文件分析信号时序和异常
- **条件赋值追踪**：显示信号赋值的条件逻辑
- **实例路径完整显示**：区分多实例场景

## 使用场景

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| 新项目分析 | ⭐⭐⭐⭐⭐ | 快速理解模块层次和信号流 |
| Debug 定位 | ⭐⭐⭐⭐⭐ | 精准追踪问题信号，比手动 grep 快 5-10 倍 |
| 代码审查 | ⭐⭐⭐⭐ | 快速理解模块接口 |
| 文档生成 | ⭐⭐⭐ | info 输出可转为文档 |
| 波形分析辅助 | ⭐⭐⭐⭐ | 配合 VCD 使用效果更好 |

## 快速安装

```bash
tar -xzf openTrace-skill.tar.gz
cd openTrace-skill
./install.sh
```

安装脚本会：
1. 提示输入 vtags 安装路径（默认 `~/vtags`）
2. 复制 vtags 源码到目标路径
3. 编译 C Parser（需要 gcc）
4. 安装 OpenCode skill 到 `~/.config/opencode/skills/openTrace-skill/`

## 系统要求

- Python 3.6+
- GCC（用于编译 Parser）
- OpenCode（使用 skill 功能）
- vcdvcd（用于 VCD 波形分析，可选）: `pip install vcdvcd`

## 使用方法

安装完成后，在 OpenCode 中可以直接使用 vtags 功能：

```
帮我分析 switch_core_top 模块的拓扑结构
追踪 signal_x 信号的源头
搜索所有包含 mng 的模块
```

OpenCode 会自动加载 openTrace-skill 并执行相应命令。

## 命令行使用

```bash
# CLI 工具会自动向上搜索 vtags.db，也可用 -db 显式指定
# 以下示例假设在 vtags.db 所在目录运行，或使用 -db 参数指定路径

# 列出顶层模块
python3 <vtags_path>/Standalone/cli.py tops

# 查看模块拓扑 (depth: 0=无限展开, 1=默认, 2/3...=指定层级)
python3 <vtags_path>/Standalone/cli.py topo <module> [depth]

# 查看模块调用追踪链 (从顶层到此模块的实例化路径)
python3 <vtags_path>/Standalone/cli.py trace <module>

# 查看模块详细信息 (IO、实例等)
python3 <vtags_path>/Standalone/cli.py info <module>

# 查看模块文件列表 (模块及所有子模块的文件)
python3 <vtags_path>/Standalone/cli.py files <module>

# 搜索模块 (支持 * 和 ? 通配符)
python3 <vtags_path>/Standalone/cli.py search "*pattern*"

# 追踪信号源 (单跳)
python3 <vtags_path>/Standalone/cli.py strace <signal> <file> <line>

# 递归追踪信号源 (自动追踪多层)
python3 <vtags_path>/Standalone/cli.py strace <signal> <file> <line> -r 5

# 追踪信号目的地 (单跳)
python3 <vtags_path>/Standalone/cli.py dtrace <signal> <file> <line>

# 递归追踪信号目的地
python3 <vtags_path>/Standalone/cli.py dtrace <signal> <file> <line> -r 0

# 获取信号的完整实例路径列表 (默认返回 5 条)
python3 <vtags_path>/Standalone/cli.py strace <signal> <file> <line> --full-path

# 指定返回数量
python3 <vtags_path>/Standalone/cli.py strace <signal> <file> <line> --full-path 10

# JSON 格式输出 (方便程序解析)
python3 <vtags_path>/Standalone/cli.py -j info <module>

# VCD 波形分析 (需要安装 vcdvcd: pip install vcdvcd)
# 列出 VCD 文件中的所有信号
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --list

# 按模式过滤信号
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --list --pattern "*clk*"

# 分析指定信号
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req

# 结合代码位置分析信号 (自动确定实例路径)
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req --file rtl/xxx.v --line 100

# JSON 格式输出
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req -j

# 导出模块依赖图
# 导出 DOT 格式 (用于 Graphviz)
python3 <vtags_path>/Standalone/cli.py export-deps <module>

# 导出 Mermaid 格式 (支持 GitHub/GitLab 渲染)
python3 <vtags_path>/Standalone/cli.py export-deps <module> --format mermaid

# 导出到文件
python3 <vtags_path>/Standalone/cli.py export-deps <module> -o deps.dot

# 指定展开深度
python3 <vtags_path>/Standalone/cli.py export-deps <module> --depth 2

# 生成 PNG 图片 (需要安装 graphviz)
python3 <vtags_path>/Standalone/cli.py export-deps <module> -o deps.dot && dot -Tpng deps.dot -o deps.png

# 查看数据库统计信息
python3 <vtags_path>/Standalone/cli.py stats
```

## 典型工作流

### Debug 场景

```bash
# 1. 发现问题信号 (仿真日志或波形中发现异常)
grep "w_tx1_req" simulation.log  # 发现始终为0

# 2. 追踪信号源
python3 <vtags_path>/Standalone/cli.py strace w_tx1_req rtl/top.v 100

# 3. 查看模块结构
python3 <vtags_path>/Standalone/cli.py topo rx_mac_mng

# 4. 定位具体代码
python3 <vtags_path>/Standalone/cli.py info swlist -j | jq '.ios'

# 5. 结合波形分析
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req

# 6. 修复问题后验证
```

### 新项目理解

```bash
# 1. 找到顶层
python3 <vtags_path>/Standalone/cli.py tops

# 2. 查看拓扑
python3 <vtags_path>/Standalone/cli.py topo switch_core_top 2

# 3. 理解关键模块
python3 <vtags_path>/Standalone/cli.py info crossbar_switch_top

# 4. 追踪关键信号
python3 <vtags_path>/Standalone/cli.py dtrace i_clk rtl/top.v 10
python3 <vtags_path>/Standalone/cli.py strace o_mac_valid rtl/top.v 50
```

## 递归追踪功能

递归追踪可以自动追踪信号的完整传播链，无需手动多次调用。

### 使用方法

```bash
# 单跳追踪 (默认，保持兼容)
python3 <vtags_path>/Standalone/cli.py strace w_tx1_req rtl/top.v 100

# 递归追踪 5 层深度
python3 <vtags_path>/Standalone/cli.py strace w_tx1_req rtl/top.v 100 -r 5

# 无限追踪 (直到终止条件)
python3 <vtags_path>/Standalone/cli.py strace w_tx1_req rtl/top.v 100 -r 0
```

### 输出示例

```
============================================================
Signal: w_tx1_req
Trace Type: source (recursive, max_depth=5)
============================================================

Chain (4 levels):
  [0] w_tx1_req (rtl/top.v:100)
        wire w_tx1_req;
  [1] ← o_tx1_req (rtl/mng.v:2669) [sure]
        .o_tx1_req(w_tx1_req),
  [2] ← w_tx_1_port_vld (rtl/swlist.v:123) [sure]
        assign w_tx_1_port_vld = i_tx_1_port_vld;
  [3] ← 1'b1 (CONSTANT) [TERMINAL - CONSTANT_BINARY]
        assign i_tx_1_port_vld = 1'b1;

Terminated: binary constant assignment
```

### 终止条件

| 终止类型 | 说明 |
|---------|------|
| 常量赋值 | 信号被赋值为常量 (如 `1'b0`, `8'hFF`) |
| 顶层端口 | 到达顶层模块的 input/output 端口 |
| 宏定义 | 信号来自 \`define 宏定义 |
| 循环引用 | 检测到信号循环依赖，输出警告 |
| 最大深度 | 达到指定的最大追踪深度 |

### 循环引用检测

当检测到循环引用时，会输出警告：

```
⚠️  CIRCULAR REFERENCE DETECTED:
  Path: w_signal_a → w_signal_b → w_signal_c → w_signal_a
  Cannot trace further to avoid infinite loop
```

### 跨模块追踪

支持 Fallback 跨模块追踪，当正常追踪失败时，在父模块实例化处搜索：

```
Chain (3 levels):
  [0] w_cpu_mac0_port_link (rx_mac_mng.v:887) [sure]
      assign w_cpu_mac0_port_link = i_cpu_mac0_port_link
  [1] i_cpu_mac0_port_link (switch_core_top.v:1126) [fallback]
      .i_cpu_mac0_port_link(i_cpu_mac0_port_link),
  [2] i_cpu_mac0_port_link (switch_core_top.v:19) [port] [TERMINAL - TOP_INPUT]
      input wire i_cpu_mac0_port_link

Terminated: top-level input port
```

## 条件赋值追踪

显示信号赋值的条件逻辑，减少手动分析 `always` 块的工作量。

### 使用方法

```bash
# 追踪信号源并显示条件
python3 <vtags_path>/Standalone/cli.py strace --show-conditions <signal> <file> <line>

# 示例
python3 <vtags_path>/Standalone/cli.py strace --show-conditions r_rxack_cnt rtl/rx_mac_mng.v 2413
```

### 输出示例

```
Signal: r_rxack_cnt
Sources:
  rx_mac_mng rtl/rx_mac_mng.v:2413 [condition: ack_cnt_rst]
    r_rxack_cnt <= 12'd0;
  rx_mac_mng rtl/rx_mac_mng.v:2416 [condition: i_mac0_tx1_ack]
    r_rxack_cnt <= r_rxack_cnt + 1'b1;
```

### 支持场景

| 场景 | 说明 |
|------|------|
| `if/elsif/else` 条件 | `always` 块中的条件赋值 |
| `case/casez/casex` | case 语句分支条件（支持简写和 begin/end 两种形式） |
| 端口连接条件 | 模块实例化时的条件连接 |

### 已知限制

| 限制 | 说明 |
|------|------|
| 递归+条件 | 递归追踪与条件追踪结合时，条件不显示 |
| 复杂条件 | 嵌套条件表达式可能无法完整显示 |

### 典型用途

1. **理解计数器逻辑**：快速定位复位条件和递增条件
2. **状态机分析**：识别状态转移条件
3. **多路选择器**：理解不同条件下的数据路径选择

## VCD 波形分析功能

openTrace-skill 支持 VCD 波形文件分析，结合信号追踪帮助定位问题。

### 功能状态

| 功能 | 命令 | 状态 | 说明 |
|------|------|------|------|
| 列出信号 | `vcd <file> --list` | ✅ 可用 | 显示 VCD 中所有信号 |
| 模式过滤 | `vcd <file> --list --pattern "*clk*"` | ✅ 可用 | 在信号名和路径中搜索 |
| 分析信号 | `vcd <file> --signal <name>` | ✅ 可用 | 智能匹配信号路径 |
| 代码定位 | `vcd <file> --signal <name> --file --line` | ✅ 可用 | 实例路径自动定位 |
| 异常检测 | 自动检测 | ✅ 可用 | 检测信号卡死、始终为 X/Z |

### 使用示例

```bash
# 列出所有信号
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --list

# 按模式过滤信号
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --list --pattern "*clk*"

# 分析指定信号
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req

# 结合代码位置分析信号 (自动确定实例路径)
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req --file rtl/xxx.v --line 100

# JSON 格式输出
python3 <vtags_path>/Standalone/cli.py vcd waveform.vcd --signal w_tx1_req -j
```

### 输出示例

```
Signal: w_tx1_req
VCD Path: switch_core_top.rx_mac_mng_inst.w_tx1_req
Match Type: exact_name
Width: 1 bit(s)

Timeline (3 transitions):
  #0: 0
  #1206000: 0
  #2400000: 0

Warnings:
  [!] Signal stuck at 0 - check driver logic
```

### Python API

```python
from Standalone import TraceAPI, VCDAnalyzer

# 初始化 API
api = TraceAPI('/path/to/vtags.db')

# 方法 1: 使用高级 API
result = api.analyze_signal_waveform(
    'waveform.vcd',
    'signal_name',
    'rtl/module.v',  # 可选，用于确定实例路径
    100              # 可选，行号
)
print(result['timeline'])       # [(time, value), ...]
print(result['anomalies'])      # 异常检测结果

# 方法 2: 使用底层 VCDAnalyzer
analyzer = VCDAnalyzer('waveform.vcd')
analyzer.parse()

# 列出所有信号
signals = analyzer.list_signals()

# 按模式过滤
clk_signals = analyzer.list_signals(pattern="*clk*")

# 查找信号 (返回匹配列表)
matches = analyzer.find_signal('clk')

# 获取时序
timeline = analyzer.get_signal_timeline('top.clk')

# 检测异常
anomalies = analyzer.detect_anomalies('top.clk')
```

## 功能状态总览

| 功能 | 状态 | 版本 | 说明 |
|------|------|------|------|
| 模块拓扑 | ✅ | v1.0 | 展示模块层次结构 |
| 模块信息 | ✅ | v1.0 | IO、参数、实例列表 |
| 模块搜索 | ✅ | v1.0 | 支持通配符 |
| 信号追踪 | ✅ | v1.0 | 单跳源/目的地追踪 |
| 递归追踪 | ✅ | v3.13 | 自动追踪完整传播链 |
| 跨模块追踪 | ✅ | v3.12 | Fallback 机制 |
| 条件赋值追踪 | ✅ | v3.12 | 显示赋值条件 |
| case 语句条件 | ✅ | v3.14 | 支持 case/casez/casex 分支条件 |
| 实例路径显示 | ✅ | v3.12 | 区分多实例场景 |
| VCD 波形分析 | ✅ | v3.12 | 时序和异常检测 |
| 顶层端口检测 | ✅ | v3.12 | 自动识别顶层 input/output |
| 依赖图导出 | ✅ | v1.0 | 导出 DOT/Mermaid/JSON 格式 |
| 统计信息 | ✅ | v3.14 | 数据库模块/实例/信号统计 |

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
openTrace-skill/
├── README.md          # 本文件
├── CHANGELOG.md       # 版本变更记录
├── CONTRIBUTING.md    # 贡献指南
├── Makefile           # 常用命令
├── requirements.txt   # Python 依赖
├── install.sh         # 安装脚本
├── skill/
│   └── SKILL.md       # OpenCode skill 定义
├── docs/              # 文档
├── examples/          # 使用示例
└── vtags/             # vtags 完整源码
    ├── Standalone/    # 独立命令行工具
    │   ├── cli.py         # 命令行入口
    │   ├── TraceAPI.py    # 追踪 API
    │   ├── SignalTrace.py # 信号追踪
    │   ├── ModuleTrace.py # 模块拓扑
    │   └── VCDAnalyzer.py # VCD 波形分析
    ├── Parser/        # C Parser
    │   ├── Parser.c       # Parser 源码
    │   └── parser         # 编译后的二进制
    ├── Lib/           # 核心库
    └── ...
```

## 版本历史

### v3.14 (当前)
- ✅ case 语句条件追踪（支持简写和 begin/end 两种形式）

### v3.13
- ✅ 递归追踪支持 maybe 分支
- ✅ 支持复杂表达式（位选、拼接、三元运算）

### v3.12
- ✅ VCD 波形分析功能
- ✅ 跨模块追踪 (Fallback 机制)
- ✅ 条件赋值追踪
- ✅ 实例路径完整显示
- ✅ 顶层端口自动检测

### v1.0
- ✅ 基础模块分析 (topo, info, files, search)
- ✅ 信号追踪 (strace, dtrace)
- ✅ JSON 输出支持

## 更多信息

- vtags 原项目: https://www.vim.org/scripts/script.php?script_id=5494
- OpenCode 文档: https://opencode.ai/docs/skills/
