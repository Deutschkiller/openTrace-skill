"""
vtags Standalone Trace API
独立于 Vim 的追踪 API，可直接作为 Python 库使用
"""

import os
import sys


class TraceAPI:
    """
    vtags 独立追踪 API

    使用示例:
        from Standalone import TraceAPI

        api = TraceAPI('/path/to/vtags.db')

        # 模块追踪
        traces = api.get_module_trace('cpu_top')

        # 模块拓扑
        topo = api.get_module_topo('cpu_top', depth=2)

        # 模块文件列表
        files = api.get_module_filelist('cpu_top')

        # 信号追踪
        sources = api.trace_signal_source('clk', 'rtl/cpu.v', 42)
        dests = api.trace_signal_dest('data_out', 'rtl/cpu.v', 100)
    """

    def __init__(self, vtags_db_path):
        """
        初始化 TraceAPI

        Args:
            vtags_db_path: vtags.db 目录路径
        """
        self.vtags_db_path = os.path.realpath(vtags_db_path.rstrip("/"))

        if not os.path.isdir(self.vtags_db_path):
            raise ValueError(f"vtags.db path not found: {self.vtags_db_path}")

        if not self.vtags_db_path.endswith("vtags.db"):
            raise ValueError(f"Path must be a vtags.db directory: {self.vtags_db_path}")

        self._G = None
        self._initialized = False

    def _init_db(self):
        """延迟初始化数据库连接"""
        if self._initialized:
            return

        vtags_install_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if vtags_install_path not in sys.path:
            sys.path.insert(0, vtags_install_path)

        import Lib.GLB as GLB

        self._G = GLB.G.copy() if GLB.G else {}

        GLB.set_vtags_db_path(self.vtags_db_path)

        new_G = GLB.init_G_from_vtagsDB(self.vtags_db_path, allow_from_glb=False)
        if not new_G:
            raise RuntimeError(
                f"Failed to initialize vtags database: {self.vtags_db_path}"
            )

        for key in new_G:
            self._G[key] = new_G[key]

        self._G["OfflineActive"] = True
        self._G["InlineActive"] = False

        from .ModuleTrace import ModuleTrace
        from .SignalTrace import SignalTrace

        self._module_trace = ModuleTrace(self._G)
        self._signal_trace = SignalTrace(self._G)

        self._initialized = True

    @property
    def G(self):
        """获取全局状态字典"""
        self._init_db()
        return self._G

    def get_module_trace(self, module_name):
        """
        获取模块调用追踪链

        Args:
            module_name: 模块名称

        Returns:
            list: 追踪链列表，每项包含:
                - chain: 调用链字符串 (如 'top.cpu_inst.cpu_top')
                - modules: 模块名列表
                - instances: 实例名列表
                - files: 文件路径列表
        """
        self._init_db()
        return self._module_trace.get_trace(module_name)

    def get_module_topo(self, module_name, depth=1, mask_threshold=None):
        """
        获取模块拓扑结构

        Args:
            module_name: 模块名称
            depth: 展开深度 (0=无限)
            mask_threshold: 实例数超过此值的模块将被折叠 (None=使用默认值)

        Returns:
            dict: 拓扑结构，包含:
                - module: 模块名
                - file: 文件路径
                - line: 定义行号
                - children: 子实例列表
        """
        self._init_db()
        return self._module_trace.get_topo(module_name, depth, mask_threshold)

    def get_module_filelist(self, module_name):
        """
        获取模块及其子模块的所有文件列表

        Args:
            module_name: 模块名称

        Returns:
            list: 文件路径列表
        """
        self._init_db()
        return self._module_trace.get_filelist(module_name)

    def get_all_top_modules(self):
        """
        获取所有顶层模块列表

        Returns:
            list: 顶层模块名列表
        """
        self._init_db()
        return self._module_trace.get_all_top_modules()

    def export_dependencies(self, module_name, depth=0, format="dot"):
        """
        导出模块依赖图

        Args:
            module_name: 模块名称
            depth: 展开深度 (0=无限)
            format: 导出格式 ('dot', 'json', 'mermaid')

        Returns:
            str: 导出的依赖图字符串
        """
        self._init_db()
        return self._module_trace.export_dependencies(module_name, depth, format)

    def trace_signal_source(
        self, signal_name, file_path, line_num, column_num=0, show_conditions=False
    ):
        """
        追踪信号源

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)
            show_conditions: 是否显示条件信息

        Returns:
            dict: 追踪结果:
                - signal_name: 信号名
                - trace_type: 'source'
                - sure: 确定的源列表
                - maybe: 可能的源列表
        """
        self._init_db()
        return self._signal_trace.trace(
            signal_name, file_path, line_num, column_num, "source", show_conditions
        )

    def trace_signal_source_recursive(
        self, signal_name, file_path, line_num, column_num=0, max_depth=5
    ):
        """
        递归追踪信号源

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)
            max_depth: 最大追踪深度 (0=无限, 默认5)

        Returns:
            dict: 递归追踪结果:
                - signal_name: 原始信号名
                - trace_type: 'source'
                - max_depth: 最大深度
                - chain: 主追踪链列表
                - maybe_branches: 可能的分支列表
                - terminated_reason: 终止原因
                - circular_path: 循环路径 (如果有)
        """
        self._init_db()
        return self._signal_trace.trace_recursive(
            signal_name, file_path, line_num, column_num, "source", max_depth
        )

    def trace_signal_dest(
        self, signal_name, file_path, line_num, column_num=0, show_conditions=False
    ):
        """
        追踪信号目的地

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)
            show_conditions: 是否显示条件信息

        Returns:
            dict: 追踪结果:
                - signal_name: 信号名
                - trace_type: 'dest'
                - sure: 确定的目的地列表
                - maybe: 可能的目的地列表
        """
        self._init_db()
        return self._signal_trace.trace(
            signal_name, file_path, line_num, column_num, "dest", show_conditions
        )

    def trace_signal_dest_recursive(
        self, signal_name, file_path, line_num, column_num=0, max_depth=5
    ):
        """
        递归追踪信号目的地

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)
            max_depth: 最大追踪深度 (0=无限, 默认5)

        Returns:
            dict: 递归追踪结果:
                - signal_name: 原始信号名
                - trace_type: 'dest'
                - max_depth: 最大深度
                - chain: 主追踪链列表
                - maybe_branches: 可能的分支列表
                - terminated_reason: 终止原因
                - circular_path: 循环路径 (如果有)
        """
        self._init_db()
        return self._signal_trace.trace_recursive(
            signal_name, file_path, line_num, column_num, "dest", max_depth
        )

    def get_signal_full_paths(
        self,
        signal_name,
        file_path,
        line_num,
        column_num=0,
        trace_type="dest",
        max_paths=5,
    ):
        """
        获取信号的完整实例路径列表

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)
            trace_type: 'source' 或 'dest' (默认 'dest')
            max_paths: 最大返回数量 (默认 5)

        Returns:
            dict: {
                "signal_name": 信号名,
                "trace_type": 追踪类型,
                "max_paths": 最大数量,
                "paths": 路径列表,
                "total_found": 总数,
                "limited": 是否达到上限
            }
        """
        self._init_db()
        return self._signal_trace.get_signal_full_paths(
            signal_name, file_path, line_num, column_num, trace_type, max_paths
        )

    def get_module_info(self, module_name):
        """
        获取模块信息

        Args:
            module_name: 模块名称

        Returns:
            dict: 模块信息，包含:
                - name: 模块名
                - file: 文件路径
                - line: 定义行号
                - ios: IO 端口列表
                - params: 参数列表
                - instances: 实例化列表
        """
        self._init_db()
        return self._module_trace.get_module_info(module_name)

    def search_module(self, pattern):
        """
        搜索匹配的模块名

        Args:
            pattern: 搜索模式 (支持通配符)

        Returns:
            list: 匹配的模块名列表
        """
        self._init_db()
        return self._module_trace.search_module(pattern)

    def load_vcd(self, vcd_path):
        """
        加载 VCD 文件

        Args:
            vcd_path: VCD 文件路径

        Returns:
            VCDAnalyzer 实例

        Raises:
            ImportError: vcdvcd 未安装
            FileNotFoundError: VCD 文件不存在
        """
        self._init_db()
        from .VCDAnalyzer import VCDAnalyzer

        analyzer = VCDAnalyzer(vcd_path, self._G)
        analyzer.parse()
        return analyzer

    def analyze_signal_waveform(
        self, vcd_path, signal_name, file_path=None, line_num=None, column_num=0
    ):
        """
        分析信号波形

        结合 Verilog 代码位置确定实例路径，查询 VCD 中的信号时序

        Args:
            vcd_path: VCD 文件路径
            signal_name: 信号名
            file_path: Verilog 文件路径 (可选，用于确定实例上下文)
            line_num: 行号 (可选)
            column_num: 列号 (可选)

        Returns:
            dict: 分析结果
                - signal_name: 信号名
                - vcd_path: VCD 中的完整路径
                - width: 位宽
                - timeline: [(time, value), ...]
                - summary: 信号摘要
                - anomalies: 异常检测
                - matched_signals: 匹配的信号列表
        """
        self._init_db()
        from .VCDAnalyzer import VCDAnalyzer

        analyzer = VCDAnalyzer(vcd_path, self._G)
        analyzer.parse()

        instance_path = ""
        if file_path and line_num is not None:
            instance_path = self._get_instance_path(file_path, line_num, column_num)

        matched_signals = analyzer.find_signal(signal_name, instance_path=instance_path)

        result = {
            "signal_name": signal_name,
            "instance_path": instance_path,
            "matched_signals": matched_signals,
            "vcd_path": None,
            "width": None,
            "timeline": [],
            "summary": None,
            "anomalies": None,
        }

        if matched_signals:
            best_match = matched_signals[0]["vcd_path"]
            result["vcd_path"] = best_match
            result["width"] = analyzer.get_signal_width(best_match)
            result["timeline"] = analyzer.get_signal_timeline(best_match)
            result["summary"] = analyzer.get_signal_summary(best_match)
            result["anomalies"] = analyzer.detect_anomalies(best_match)

        return result

    def _get_instance_path(self, file_path, line_num, column_num=0):
        """
        根据文件位置获取实例路径

        Args:
            file_path: 文件路径
            line_num: 行号
            column_num: 列号

        Returns:
            str: 实例路径 (如 "top.inst1.inst2")
        """
        import Lib.FileInfLib as FileInfLib

        file_path = os.path.realpath(file_path)

        module_io_inf = FileInfLib.get_module_io_inf_from_pos(
            file_path, (line_num, column_num)
        )
        module_inf = module_io_inf.get("module_inf")

        if not module_inf:
            return ""

        module_name = module_inf["module_name_sr"]["str"]

        traces = self.get_module_trace(module_name)
        if traces:
            trace = traces[0]
            if trace.get("instances"):
                return ".".join(trace["instances"])

        return module_name

    def list_vcd_signals(self, vcd_path, pattern=None):
        """
        列出 VCD 文件中的信号

        Args:
            vcd_path: VCD 文件路径
            pattern: 通配符模式 (可选)

        Returns:
            list: 信号名列表
        """
        self._init_db()
        from .VCDAnalyzer import VCDAnalyzer

        analyzer = VCDAnalyzer(vcd_path, self._G)
        analyzer.parse()

        return analyzer.list_signals(pattern)

    def get_stats(self):
        """
        获取数据库统计信息

        Returns:
            dict: {
                "database": "/path/to/vtags.db",
                "modules": 156,
                "instances": 892,
                "signals": 15420,
                "files": 85,
                "last_updated": "2026-03-26"
            }
        """
        self._init_db()
        from datetime import datetime

        stats = {
            "database": self.vtags_db_path,
            "modules": 0,
            "instances": 0,
            "signals": 0,
            "files": 0,
            "last_updated": None,
        }

        pub_dir = os.path.join(self.vtags_db_path, "parser_out", "pub")
        if os.path.isdir(pub_dir):
            parser_files = [
                f
                for f in os.listdir(pub_dir)
                if f.startswith("parser_") and f.endswith(".py")
            ]
            stats["modules"] = len(parser_files)

            for f in parser_files:
                filepath = os.path.join(pub_dir, f)
                try:
                    with open(filepath, "r") as fp:
                        content = fp.read()
                        stats["instances"] += content.count("'submodule_name_sr'")
                        stats["signals"] += content.count("'name_sr'") - content.count(
                            "'module_name_sr'"
                        )
                except:
                    pass

            stats["files"] = stats["modules"]

        db_path = self.vtags_db_path
        if os.path.isdir(db_path):
            log_path = os.path.join(db_path, "vtags_db.log")
            if os.path.exists(log_path):
                mtime = os.path.getmtime(log_path)
            else:
                mtime = os.path.getmtime(db_path)
            stats["last_updated"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

        return stats
