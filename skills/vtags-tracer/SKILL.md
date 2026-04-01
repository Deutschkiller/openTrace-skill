---
name: vtags-tracer
description: Verilog HDL 代码追踪工具。支持模块拓扑、信号源/目的地追踪、模块搜索、依赖导出等功能。当用户需要分析 Verilog 代码结构、追踪信号来源或去向、查看模块层级时调用。
---

# vtags-tracer

Verilog HDL 代码追踪工具，提供模块拓扑、信号追踪、模块搜索、依赖导出等功能。

## 路径发现（AI 必读）

**重要：使用本 skill 前，必须先确定 `VTAGS_PATH`。**

### 自动发现顺序

| 优先级 | 方法 | 命令 |
|--------|------|------|
| 1 | 环境变量 | `echo $VTAGS_PATH` |
| 2 | 项目根目录下的 vtags/ | `git rev-parse --show-toplevel` + `/vtags` |
| 3 | 当前工作目录递归查找 | `find . -maxdepth 3 -type d -name "vtags"` |
| 4 | 向上查找父目录 | `find .. -maxdepth 2 -type d -name "vtags"` |
| 5 | 用户主目录 | `~/vtags` |

### 发现脚本

```bash
# 优先级 1: 环境变量
[ -n "$VTAGS_PATH" ] && echo "$VTAGS_PATH" && exit 0

# 优先级 2: 项目根目录下的 vtags/
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -n "$PROJECT_ROOT" ] && [ -d "$PROJECT_ROOT/vtags" ] && echo "$PROJECT_ROOT/vtags" && exit 0

# 优先级 3: 当前工作目录递归查找
FOUND=$(find . -maxdepth 3 -type d -name "vtags" 2>/dev/null | head -1)
[ -n "$FOUND" ] && echo "$FOUND" && exit 0

# 优先级 4: 向上查找父目录
FOUND=$(find .. -maxdepth 2 -type d -name "vtags" 2>/dev/null | head -1)
[ -n "$FOUND" ] && echo "$FOUND" && exit 0

# 优先级 5: 用户主目录
[ -d ~/vtags ] && echo ~/vtags && exit 0

# 未找到
echo "ERROR: vtags not found" >&2
exit 1
```

### AI 执行流程

1. **发现路径**：运行上述发现脚本，获取 `VTAGS_PATH`
2. **验证路径**：`[ -f "$VTAGS_PATH/Standalone/cli.py" ]`
3. **缓存路径**：在当前会话中记住路径，避免重复查找
4. **执行命令**：将文档中 `{{VTAGS_PATH}}` 替换为实际路径

### 错误处理

如果所有方法都找不到：

```
❌ 无法找到 vtags 工具

请执行以下任一操作：
1. 设置环境变量：export VTAGS_PATH=/path/to/vtags
2. 在项目根目录创建 vtags/ 目录
3. 安装 vtags 到 ~/vtags/
```

---

## 安装路径

- **vtags 根目录**: `<VTAGS_PATH>/` (通过上述"路径发现"确定)
- **CLI 工具**: `<VTAGS_PATH>/Standalone/cli.py`
- **文档示例**: 使用 `{{VTAGS_PATH}}` 占位符，AI 需替换为实际路径

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
