---
name: vtags-standalone
description: Verilog HDL 代码导航工具，独立于 Vim。支持模块拓扑、信号追踪、模块搜索等功能。当用户需要分析 Verilog 代码、追踪信号、查看模块层级时调用。
---

# vtags-standalone

vtags-standalone 是一个独立于 Vim 的 Verilog 代码分析工具，提供模块拓扑、信号追踪、模块搜索等功能。

## 安装路径

- **vtags 根目录**: `{{VTAGS_PATH}}/`
- **CLI 工具**: `{{VTAGS_PATH}}/Standalone/cli.py`

## 使用前提

1. 需要有已生成的 vtags.db 数据库
2. 使用 `-db` 参数指定数据库路径

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

### strace - 信号源追踪
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> strace <signal> <file> <line> [column] [-r depth]
```
- `signal`: 信号名称
- `file`: 文件路径
- `line`: 行号 (从 1 开始)
- `column`: 列号 (从 0 开始，可选)
- `-r depth`: 递归追踪深度 (0=无限, 1=单跳, 默认=1)

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
python3 {{VTAGS_PATH}}/Standalone/cli.py strace w_tx1_req rtl/top.v 100 -r 5

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
