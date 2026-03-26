# vtags-standalone

Verilog HDL 代码导航工具，独立于 Vim。支持模块拓扑、模块追踪、信号追踪、模块搜索、VCD 波形分析等功能。

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
# CLI 工具会自动向上搜索 vtags.db，也可用 -db 显式指定
# python3 <vtags_path>/Standalone/cli.py -db ./vtags.db <command>

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

递归追踪会在以下情况终止：

| 终止类型 | 说明 |
|---------|------|
| 常量赋值 | 信号被赋值为常量 (如 `1'b0`, `8'hFF`) |
| 顶层端口 | 到达顶层模块的 input/output 端口 |
| 宏定义 | 信号来自 `define 宏定义 |
| 循环引用 | 检测到信号循环依赖，输出警告 |
| 最大深度 | 达到指定的最大追踪深度 |

### 循环引用检测

当检测到循环引用时，会输出警告：

```
⚠️  CIRCULAR REFERENCE DETECTED:
  Path: w_signal_a → w_signal_b → w_signal_c → w_signal_a
  Cannot trace further to avoid infinite loop
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

## VCD 波形分析功能

vtags-standalone 支持 VCD 波形文件分析，结合信号追踪帮助定位问题。

### 安装依赖

```bash
pip install vcdvcd
```

### 功能特性

- 列出 VCD 文件中的所有信号
- 按模式过滤信号（支持在信号名和路径中搜索）
- 分析信号变化时序
- 检测信号异常（如始终为 0/X/Z）
- 结合 Verilog 代码位置自动确定实例路径
- 解析 VCD scope 层级结构

### 功能状态

| 功能 | 命令 | 状态 | 说明 |
|------|------|------|------|
| 列出信号 | `vcd <file> --list` | ✅ 可用 | 显示 VCD 中所有信号 |
| 模式过滤 | `vcd <file> --list --pattern "*clk*"` | ✅ 可用 | 在信号名和路径中搜索 |
| 分析信号 | `vcd <file> --signal <name>` | ✅ 可用 | 智能匹配信号路径 |
| 代码定位 | `vcd <file> --signal <name> --file --line` | ⚠️ 部分 | 实例路径自动定位 |
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

# 获取标识符映射
id_mapping = analyzer.get_id_mapping()

# 获取 scope 层级
scopes = analyzer.get_scopes()
```

### 限制与注意事项

1. **信号名匹配**：VCD 中的信号路径可能与 Verilog 实例路径不完全一致，建议使用 `--file --line` 参数提供上下文
2. **大型 VCD 文件**：解析大型 VCD 文件可能较慢，建议先用 `--list` 查看规模
3. **标识符映射**：部分仿真器生成的 VCD 使用简短标识符，已支持解析但匹配可能需要调整

## 更多信息

- vtags 原项目: https://github.com/user/vtags
- OpenCode 文档: https://opencode.ai/docs/skills/
