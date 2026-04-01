---
name: vcd-analyzer
description: VCD 波形分析工具。支持信号列表查询、波形时序分析、异常检测等功能。当用户需要分析仿真波形、查看信号变化时序、检测信号异常时调用。
---

# vcd-analyzer

VCD 波形分析工具，支持信号列表查询、波形时序分析、异常检测等功能。

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

## 依赖安装

```bash
pip install vcdvcd
```

## 使用前提

1. 需要有已生成的 vtags.db 数据库
2. 使用 `-db` 参数指定数据库路径
3. 需要有 VCD 波形文件

## 使用规范

### 重要限制

1. **禁止自行解析 VCD 文件**
   - 不允许使用 Python 代码自行解析 VCD 文件
   - 必须使用 vcd-analyzer 提供的 CLI 命令或 Python API
   - VCD 分析必须通过 `vcd` 命令或 `TraceAPI.analyze_signal_waveform()` 方法

2. **功能限制反馈**
   - 如果 vcd-analyzer 的功能无法满足需求，必须向用户反馈
   - 不要尝试用其他方式绕过限制
   - 反馈格式：「vcd-analyzer 当前不支持 XXX 功能，建议...」

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
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <vtags_db_path> vcd <vcd_file> [options]
```

## vcd 命令

### 信号路径格式

`--signal` 参数支持以下格式：

1. **完整路径**: `tb_vp_004.o_cpu_mac0_axi_data_last`
2. **信号名**: `o_cpu_mac0_axi_data_last` (推荐)
3. **部分匹配**: `cpu_mac0_axi_data_last`

**注意**: 如果信号名在多个位置存在，建议使用完整路径或结合 `--file --line` 参数。

### 列出 VCD 中的信号
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --list
```

### 按模式过滤信号
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --list --pattern "*clk*"
```

### 分析指定信号
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

### 结合代码位置分析
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> vcd <vcd_file> --signal <signal> --file <verilog_file> --line <line_num>
```

会自动根据文件位置确定实例路径，精确匹配 VCD 中的信号。

**说明**: `--file --line` 参数可选，用于结合 Verilog 代码位置推断 VCD 中的信号实例路径。如需精确的代码位置信息，可配合 `vtags-tracer` skill 使用。

### JSON 格式输出
```bash
python3 {{VTAGS_PATH}}/Standalone/cli.py -db <db_path> -j vcd <vcd_file> --signal <signal_name>
```

## Python API

```python
import sys
sys.path.insert(0, '{{VTAGS_PATH}}')
from Standalone import TraceAPI

# 初始化
api = TraceAPI('/path/to/vtags.db')

# VCD 波形分析
result = api.analyze_signal_waveform('waveform.vcd', 'signal_name', 'rtl/module.v', line)
print(result['timeline'])   # [(time, value), ...]
print(result['anomalies'])  # 异常检测结果

# 列出 VCD 信号
signals = api.list_vcd_signals('waveform.vcd', pattern='*clk*')

# 加载 VCD 文件（高级用法）
analyzer = api.load_vcd('waveform.vcd')

# 获取信号时序
timeline = analyzer.get_signal_timeline('top.inst.signal')

# 获取信号位宽
width = analyzer.get_signal_width('top.inst.signal')

# 检测异常
anomalies = analyzer.detect_anomalies('top.inst.signal')

# 查找信号（模糊匹配）
matched = analyzer.find_signal('signal_name', instance_path='top.inst')
```

## 异常检测

vcd-analyzer 会自动检测以下信号异常：

| 异常类型 | 说明 |
|----------|------|
| `stuck_at_0` | 信号一直为 0 |
| `stuck_at_1` | 信号一直为 1 |
| `stuck_at_x` | 信号一直为 X (未知) |
| `stuck_at_z` | 信号一直为 Z (高阻) |
| `never_changed` | 信号从未变化 |

## 常见用例

### 查看信号波形
```bash
# 列出 VCD 中的所有时钟信号
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db vcd wave.vcd --list --pattern "*clk*"

# 分析特定信号
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db vcd wave.vcd --signal w_tx1_req
```

### 调试信号异常
```bash
# 分析信号，查看是否有异常
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db vcd wave.vcd --signal stuck_signal

# 输出示例：
# Warnings:
#   [!] Signal stuck at 0 - check driver logic
```

### 结合代码追踪
```bash
# 1. 使用 vtags-tracer 找到信号定义位置
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db strace signal_name rtl/top.v 100

# 2. 结合代码位置分析波形
python3 {{VTAGS_PATH}}/Standalone/cli.py -db ./vtags.db vcd wave.vcd --signal signal_name --file rtl/module.v --line 50
```
