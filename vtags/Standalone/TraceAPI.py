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

    def trace_signal_source(self, signal_name, file_path, line_num, column_num=0):
        """
        追踪信号源

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)

        Returns:
            dict: 追踪结果:
                - signal_name: 信号名
                - trace_type: 'source'
                - sure: 确定的源列表
                - maybe: 可能的源列表
                每项包含:
                    - file: 文件路径
                    - line: 行号
                    - column: 列号
                    - code: 代码行
                    - module: 所在模块
        """
        self._init_db()
        return self._signal_trace.trace(
            signal_name, file_path, line_num, column_num, "source"
        )

    def trace_signal_dest(self, signal_name, file_path, line_num, column_num=0):
        """
        追踪信号目的地

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed, 可选)

        Returns:
            dict: 追踪结果:
                - signal_name: 信号名
                - trace_type: 'dest'
                - sure: 确定的目的地列表
                - maybe: 可能的目的地列表
        """
        self._init_db()
        return self._signal_trace.trace(
            signal_name, file_path, line_num, column_num, "dest"
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
