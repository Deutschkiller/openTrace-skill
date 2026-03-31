---
name: openTrace-skill
description: Verilog HDL 代码导航工具，独立于 Vim。支持模块拓扑、信号追踪、模块搜索等功能。当用户需要分析 Verilog 代码、追踪信号、查看模块层级时调用。
---

# openTrace-skill

openTrace-skill 是一个独立于 Vim 的 Verilog 代码分析工具，提供模块拓扑、信号追踪、模块搜索等功能。

## 安装路径

- **vtags 根目录**: `{{VTAGS_PATH}}/`
- **CLI 工具**: `{{VTAGS_PATH}}/Standalone/cli.py`

## 使用前提

1. 需要有已生成的 vtags.db 数据库
2. 使用 `-db` 参数指定数据库路径

## 使用规范

### 重要限制

1. **禁止自行解析 VCD 文件**
   - 不允许使用 Python 代码自行解析 VCD 文件
   - 必须使用 openTrace-skill 提供的 CLI 命令或 Python API
   - VCD 分析必须通过 `vcd` 命令或 `TraceAPI.analyze_signal_waveform()` 方法

2. **功能限制反馈**
   - 如果 openTrace-skill 的功能无法满足需求，必须向用户反馈
   - 不要尝试用其他方式绕过限制
   - 反馈格式：「openTrace-skill 当前不支持 XXX 功能，建议...」

### 正确使用方式

```bash
# 正确：使用 CLI 命令
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --signal <name>

# 正确：使用 Python API
result = api.analyze_signal_waveform('waveform.vcd', 'signal_name')

# 错误：不要自己写代码解析 VCD
with open('waveform.vcd', 'r') as f:  # ❌ 禁止
    content = f.read()
    # 解析 VCD 内容...
```

## 命令格式

```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <vtags_db_path> <command> [args]
```

## 命令列表

### tops - 列出顶层模块
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> tops
```

输出示例：
```
0: switch_core_top
1: rx_port_mng
2: tx_mac_port_mng
```

### topo - 模块拓扑结构
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> topo <module> [depth]
```
- `depth`: 0=无限展开, 1=默认, 2/3...=指定层级

输出示例：
```
switch_core_top
    rx_mac_mng_inst(rx_mac_mng)
    tsn_cb_top_inst(tsn_cb_top)
        u_vectory_recovery_0(vectory_recovery)
        u_match_recovery_0(match_recovery)
    crossbar_switch_top_inst(crossbar_switch_top)
```

### info - 模块详细信息
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> info <module>
```

输出示例：
```
Module: switch_core_top
File: /path/to/switch_core_top.v
Line: 3

IOs (189):
  input   i_clk
  input   i_rst
  output  o_data

Instances (5):
  rx_mac_mng_inst      rx_mac_mng
  tsn_cb_top_inst      tsn_cb_top
```

### files - 模块文件列表
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> files <module>
```

输出：模块及其子模块的所有文件路径列表

### search - 搜索模块名
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> search <pattern>
```
- `pattern`: 支持 `*` 和 `?` 通配符

示例：
```bash
# 搜索所有包含 mng 的模块
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db search "*mng*"

# 搜索以 _top 结尾的模块
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db search "*_top"
```

### trace - 模块调用追踪链
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> trace <module>
```

显示从顶层模块到此模块的实例化路径。

输出示例：
```
switch_core_top
  └── rx_mac_mng_inst(rx_mac_mng)
        └── target_module_inst(target_module)
```

### strace - 信号源追踪
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> strace <signal> <file> <line> [column] [-r depth]
```
- `signal`: 信号名称
- `file`: 文件路径
- `line`: 行号 (从 1 开始)
- `column`: 列号 (从 0 开始，可选)
- `-r depth`: 递归追踪深度 (0=无限, 1=单跳, 默认=1)
- `--full-path`: 获取信号的完整实例路径列表 (默认 5 条)
- `--full-path N`: 指定返回路径数量

输出示例：
```
============================================================
Signal: i_clk
Trace Type: source
============================================================

Sure source:
  switch_core_top /path/to/switch_core_top.v:15
        input wire i_clk, // 250MHz
```

递归追踪示例：
```bash
# 递归追踪 5 层深度
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db strace w_tx1_req rtl/top.v 100 -r 5

# 输出示例:
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

#### 跨模块追踪

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

#### 循环引用检测

当检测到循环引用时，会输出警告：

```
⚠️  CIRCULAR REFERENCE DETECTED:
  Path: w_signal_a → w_signal_b → w_signal_c → w_signal_a
  Cannot trace further to avoid infinite loop
```

### dtrace - 信号目的地追踪
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> dtrace <signal> <file> <line> [column] [-r depth]
```
- 参数同 strace

输出示例：
```
============================================================
Signal: i_rst
Trace Type: dest
============================================================

Sure dest:
  tsn_cb_top:u_vectory_recovery_0(vectory_recovery) /path/to/tsn_cb_top.v:153
        .i_rst (i_rst),
  tsn_cb_top:u_match_recovery_0(match_recovery) /path/to/tsn_cb_top.v:205
        .i_rst (i_rst),
  ```

### --show-conditions - 条件赋值追踪

显示信号赋值的条件逻辑，支持 `if/elsif/else` 和 `case` 语句。

```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> strace --show-conditions <signal> <file> <line>
```

输出示例：
```
Signal: r_rxack_cnt
Sources:
  rx_mac_mng rtl/rx_mac_mng.v:2413 [condition: ack_cnt_rst]
    r_rxack_cnt <= 12'd0;
  rx_mac_mng rtl/rx_mac_mng.v:2416 [condition: i_mac0_tx1_ack]
    r_rxack_cnt <= r_rxack_cnt + 1'b1;
```

case 语句示例：
```verilog
case (state)
  IDLE: next_state = ACTIVE;
  ACTIVE: begin
    next_state = DONE;
  end
  default: next_state = IDLE;
endcase
```

输出：
```
Signal: next_state
Sources:
  fsm rtl/fsm.v:10 [condition: state == IDLE]
    next_state = ACTIVE;
  fsm rtl/fsm.v:12 [condition: state == ACTIVE]
    next_state = DONE;
  fsm rtl/fsm.v:15 [condition: state == default]
    next_state = IDLE;
```

支持场景：
- `if/elsif/else` 条件
- `case/casez/casex` 语句（支持简写和 begin/end 两种形式）

已知限制：
- 递归追踪与条件追踪结合时，条件不显示
- 嵌套条件表达式可能无法完整显示

典型用途：
1. **理解计数器逻辑**：快速定位复位条件和递增条件
2. **状态机分析**：识别状态转移条件
3. **多路选择器**：理解不同条件下的数据路径选择

### -j JSON 格式输出
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> -j <command> ...
```

示例：
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db -j info switch_core_top
```

输出：
```json
{
  "name": "switch_core_top",
  "file": "/path/to/switch_core_top.v",
  "line": 2,
  "ios": [...],
  "instances": [...]
}
```

### vcd - VCD 波形分析

分析 VCD 波形文件，结合信号追踪定位问题。需要先安装依赖：

```bash
pip install vcdvcd
```

#### 信号路径格式

`--signal` 参数支持以下格式：

1. **完整路径**: `tb_vp_004.o_cpu_mac0_axi_data_last`
2. **信号名**: `o_cpu_mac0_axi_data_last` (推荐)
3. **部分匹配**: `cpu_mac0_axi_data_last`

**注意**: 如果信号名在多个位置存在，建议使用完整路径或结合 `--file --line` 参数。

#### 列出 VCD 中的信号
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --list
```

#### 按模式过滤信号
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --list --pattern "*clk*"
```

#### 分析指定信号
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --signal <signal_name>
```

输出示例：
```
Signal: w_tx1_req
VCD Path: switch_core_top.rx_mac_mng_inst.w_tx1_req
Width: 1 bit(s)

Timeline (3 transitions):
  #0: 0
  #1206000: 0
  #2400000: 0

Warnings:
  [!] Signal stuck at 0 - check driver logic
```

#### 结合代码位置分析
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --signal <signal> --file <verilog_file> --line <line_num>
```

会自动根据文件位置确定实例路径，精确匹配 VCD 中的信号。

### export-deps - 导出模块依赖图

导出模块依赖关系，支持多种格式。

```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> export-deps <module> [--format FORMAT] [--depth DEPTH] [-o OUTPUT]
```

参数：
- `--format`: 导出格式 (dot/json/mermaid，默认 dot)
- `--depth`: 展开深度 (0=无限，默认 0)
- `-o`: 输出文件 (默认 stdout)

#### 导出 DOT 格式

```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> export-deps switch_core_top

# 输出示例:
digraph module_deps {
    rankdir=TB;
    node [shape=box, style=filled, fillcolor=lightblue];

    switch_core_top [label="switch_core_top\nswitch_core_top.v"];
    rx_mac_mng [label="rx_mac_mng\nrx_mac_mng.v"];
    tsn_cb_top [label="tsn_cb_top\ntsn_cb_top.v"];

    switch_core_top -> rx_mac_mng [label="rx_mac_mng_inst"];
    switch_core_top -> tsn_cb_top [label="tsn_cb_top_inst"];
}
```

#### 生成图片

```bash
# 导出 DOT 文件
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> export-deps switch_core_top -o deps.dot

# 使用 Graphviz 生成 PNG
dot -Tpng deps.dot -o deps.png
```

#### 导出 Mermaid 格式

```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> export-deps switch_core_top --format mermaid

# 输出示例:
graph TD
    switch_core_top -->["rx_mac_mng_inst"] rx_mac_mng
    switch_core_top -->["tsn_cb_top_inst"] tsn_cb_top
```

Mermaid 格式支持 GitHub/GitLab Markdown 直接渲染。

### stats - 数据库统计信息

```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> stats
```

输出示例：
```
Database: /path/to/vtags.db
  Modules: 1145
  Instances: 1955
  Signals: 30172
  Files: 1145
  Last updated: 2026-03-26
```

## Python API

```python
import sys
sys.path.insert(0, '{{VTAGS_PATH}}')
from Standalone import TraceAPI

# 初始化
api = TraceAPI('/path/to/vtags.db')

# 获取顶层模块
tops = api.get_all_top_modules()

# 获取模块拓扑
topo = api.get_module_topo('module_name', depth=2)

# 获取模块信息
info = api.get_module_info('module_name')

# 获取模块文件列表
files = api.get_module_filelist('module_name')

# 搜索模块
modules = api.search_module('*_mng*')

# 追踪信号源 (line 从 0 开始)
sources = api.trace_signal_source('signal_name', '/path/to/file.v', line, column)

# 追踪信号目的地
dests = api.trace_signal_dest('signal_name', '/path/to/file.v', line, column)

# 递归追踪信号源 (自动追踪多层)
chain = api.trace_signal_source_recursive('signal_name', '/path/to/file.v', line, column, max_depth=5)

# 递归追踪信号目的地
chain = api.trace_signal_dest_recursive('signal_name', '/path/to/file.v', line, column, max_depth=5)

# 获取信号完整实例路径
paths = api.get_signal_full_paths('signal_name', '/path/to/file.v', line, column, trace_type='source', max_paths=5)

# VCD 波形分析
result = api.analyze_signal_waveform('waveform.vcd', 'signal_name', 'rtl/module.v', line)
print(result['timeline'])   # [(time, value), ...]
print(result['anomalies'])  # 异常检测结果

# 列出 VCD 信号
signals = api.list_vcd_signals('waveform.vcd', pattern='*clk*')

# 导出模块依赖图
dot_output = api.export_dependencies('module_name', depth=0, format='dot')
mermaid_output = api.export_dependencies('module_name', depth=2, format='mermaid')
json_output = api.export_dependencies('module_name', format='json')

# 获取数据库统计信息
stats = api.get_stats()
print(f"Modules: {stats['modules']}, Instances: {stats['instances']}")
```

## 生成 vtags.db 数据库

### 1. 编译 C Parser (首次使用)
```bash
cd {{VTAGS_PATH}}/Parser/
gcc Parser.c -o parser
```

### 2. 创建文件列表
```bash
cd <project_directory>
find . -name "*.v" > design.f
```

### 3. 生成数据库
```bash
python3 {{VTAGS_PATH}}/vtags.py -f design.f
```

数据库将生成在当前目录的 `vtags.db/` 下。

## 常见用例

### 分析新项目
```bash
# 1. 找到顶层模块
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db tops

# 2. 查看顶层模块结构
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db topo top_module 0

# 3. 查看模块 IO
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db info top_module
```

### 追踪信号
```bash
# 追踪时钟信号源
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db strace clk rtl/top.v 10

# 追踪数据信号目的地
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db dtrace data_out rtl/top.v 100
```

### 搜索相关模块
```bash
# 搜索管理模块
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db search "*_mng"

# 搜索仲裁模块
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db search "*arbiter*"
```
