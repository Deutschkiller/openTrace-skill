"""
VCD 波形分析模块
结合 vtags 数据库实现 Verilog 信号与 VCD 波形的关联分析
"""

import os
import re
import fnmatch

try:
    from vcdvcd import VCDVCD

    VCDVCD_AVAILABLE = True
except ImportError:
    VCDVCD_AVAILABLE = False
    VCDVCD = None


class VCDAnalyzer:
    """
    VCD 波形分析器

    功能:
    - 解析 VCD 文件
    - 建立信号路径映射 (标识符 -> 信号名)
    - 提供信号时序查询
    - 检测信号异常
    """

    def __init__(self, vcd_path, G=None):
        """
        初始化 VCD 分析器

        Args:
            vcd_path: VCD 文件路径
            G: vtags 全局状态字典 (可选)
        """
        if not VCDVCD_AVAILABLE:
            raise ImportError(
                "vcdvcd is required for VCD analysis.\n"
                "Install it with: pip install vcdvcd"
            )

        self.vcd_path = os.path.realpath(vcd_path)
        self._G = G
        self._vcd = None
        self._timescale = None
        self._signals = {}
        self._signal_tree = {}
        self._id_to_signal = {}
        self._signal_to_id = {}
        self._scopes = {}
        self._raw_var_definitions = []

        if not os.path.isfile(self.vcd_path):
            raise FileNotFoundError(f"VCD file not found: {self.vcd_path}")

    def parse(self):
        """
        解析 VCD 文件

        Returns:
            self (支持链式调用)
        """
        self._vcd = VCDVCD(self.vcd_path)

        self._timescale = self._vcd.timescale

        for var_id, signal in self._vcd.data.items():
            references = (
                signal.references if hasattr(signal, "references") else [var_id]
            )
            for ref in references:
                self._signals[ref] = {
                    "name": ref,
                    "size": signal.size,
                    "tv": signal.tv,
                    "signal_obj": signal,
                    "var_id": var_id,
                }
            self._id_to_signal[var_id] = references[0] if references else var_id
            for ref in references:
                self._signal_to_id[ref] = var_id

        self._parse_vcd_raw()
        self._build_signal_tree()

        return self

    def _parse_vcd_raw(self):
        """
        解析 VCD 原始内容，提取标识符映射和 scope 层级
        """
        try:
            with open(self.vcd_path, "r", errors="ignore") as f:
                content = f.read()
        except Exception:
            return

        var_pattern = re.compile(
            r"\$var\s+(\w+)\s+(\d+)\s+(\S+)\s+(\S+?)(?:\s+\S+)?\s*\$end"
        )
        for match in var_pattern.finditer(content):
            var_type, size, var_id, var_name = match.groups()
            self._id_to_signal[var_id] = var_name
            self._signal_to_id[var_name] = var_id
            self._raw_var_definitions.append(
                {
                    "type": var_type,
                    "size": int(size),
                    "id": var_id,
                    "name": var_name,
                }
            )

        scope_stack = []
        scope_pattern = re.compile(r"\$scope\s+(\S+)\s+(\S+)\s+\$end")
        upscope_pattern = re.compile(r"\$upscope\s+\$end")

        for line in content.split("\n"):
            scope_match = scope_pattern.search(line)
            if scope_match:
                scope_type, scope_name = scope_match.groups()
                scope_stack.append(scope_name)
                full_path = ".".join(scope_stack)
                if full_path not in self._scopes:
                    self._scopes[full_path] = {
                        "type": scope_type,
                        "name": scope_name,
                        "signals": [],
                    }

            upscope_match = upscope_pattern.search(line)
            if upscope_match and scope_stack:
                scope_stack.pop()

    def _build_signal_tree(self):
        """
        构建信号层级树结构

        将 VCD 信号路径解析为树结构，便于查找
        例如: "top.inst1.clk" -> {top: {inst1: {clk: signal}}}
        """
        for signal_name in self._signals:
            parts = signal_name.split(".")
            current = self._signal_tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = self._signals[signal_name]
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

    def get_timescale(self):
        """获取时间刻度"""
        return self._timescale

    def list_signals(self, pattern=None):
        """
        列出所有信号

        Args:
            pattern: 通配符模式 (可选，支持在信号名和完整路径中搜索)

        Returns:
            list: 信号名列表
        """
        signals = list(self._signals.keys())

        if pattern:
            signals = self._search_signals_by_pattern(pattern)

        return sorted(signals)

    def _search_signals_by_pattern(self, pattern):
        """
        按模式搜索信号，支持在完整路径、信号名和 $var 定义中搜索

        Args:
            pattern: 通配符模式

        Returns:
            list: 匹配的信号路径列表
        """
        results = set()

        regex = fnmatch.translate(pattern)
        regex_obj = re.compile(regex, re.IGNORECASE)

        for vcd_path in self._signals:
            if regex_obj.match(vcd_path):
                results.add(vcd_path)
                continue

            signal_name = vcd_path.split(".")[-1]
            if fnmatch.fnmatch(signal_name, pattern):
                results.add(vcd_path)
                continue

            for part in vcd_path.split("."):
                if fnmatch.fnmatch(part, pattern):
                    results.add(vcd_path)
                    break

        for var_def in self._raw_var_definitions:
            if fnmatch.fnmatch(var_def["name"], pattern):
                for vcd_path in self._signals:
                    if vcd_path.endswith("." + var_def["name"]):
                        results.add(vcd_path)

        return list(results)

    def get_signal_names_only(self):
        """
        获取所有信号名（不含路径前缀）

        Returns:
            set: 信号名集合
        """
        names = set()
        for vcd_path in self._signals:
            signal_name = vcd_path.split(".")[-1]
            names.add(signal_name)
        return names

    def get_scopes(self):
        """
        获取所有 scope 层级

        Returns:
            dict: scope 信息字典
        """
        return self._scopes

    def get_id_mapping(self):
        """
        获取标识符到信号名的映射

        Returns:
            dict: {id: signal_name}
        """
        return self._id_to_signal

    def find_signal(self, signal_name, module_name=None, instance_path=None):
        """
        查找信号，支持模糊匹配和 scope 层级匹配

        Args:
            signal_name: 信号名
            module_name: 模块名 (可选，用于上下文)
            instance_path: 实例路径 (可选，如 "top.inst1.inst2")

        Returns:
            list: 匹配的信号路径列表 [{vcd_path, score, match_type}, ...]
        """
        results = []

        exact_matches = self._find_exact_matches(signal_name, instance_path)
        if exact_matches:
            return exact_matches

        for vcd_path in self._signals:
            score, match_type = self._calculate_match_score_v2(
                signal_name, vcd_path, instance_path
            )
            if score > 0:
                results.append(
                    {"vcd_path": vcd_path, "score": score, "match_type": match_type}
                )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:20]

    def _find_exact_matches(self, signal_name, instance_path=None):
        """
        查找精确匹配

        Args:
            signal_name: 信号名或完整路径
            instance_path: 实例路径

        Returns:
            list: 精确匹配结果列表，或 None
        """
        exact_matches = []

        for vcd_path in self._signals:
            # 优先：完整路径精确匹配
            if vcd_path == signal_name:
                return [
                    {
                        "vcd_path": vcd_path,
                        "score": 100,
                        "match_type": "exact_full_path",
                    }
                ]

            # 信号名匹配（去除路径前缀）
            vcd_signal_name = vcd_path.split(".")[-1]

            if vcd_signal_name != signal_name:
                continue

            if instance_path:
                normalized_instance = instance_path.rstrip(".")
                vcd_prefix = ".".join(vcd_path.split(".")[:-1])

                if vcd_prefix == normalized_instance:
                    return [
                        {
                            "vcd_path": vcd_path,
                            "score": 100,
                            "match_type": "exact_with_path",
                        }
                    ]

                if (
                    normalized_instance in vcd_prefix
                    or vcd_prefix in normalized_instance
                ):
                    exact_matches.append(
                        {
                            "vcd_path": vcd_path,
                            "score": 90,
                            "match_type": "exact_partial_path",
                        }
                    )
            else:
                exact_matches.append(
                    {"vcd_path": vcd_path, "score": 95, "match_type": "exact_name"}
                )

        return exact_matches[:1] if exact_matches else None

    def _calculate_match_score_v2(self, signal_name, vcd_path, instance_path=None):
        """
        计算信号匹配分数 (改进版)

        Args:
            signal_name: 目标信号名
            vcd_path: VCD 信号路径
            instance_path: 实例路径 (可选)

        Returns:
            tuple: (score, match_type)
        """
        score = 0
        match_type = "partial"

        vcd_signal_name = vcd_path.split(".")[-1]
        path_parts = vcd_path.split(".")

        if vcd_signal_name == signal_name:
            score += 60
            match_type = "name_exact"
        elif vcd_signal_name.startswith(signal_name):
            score += 40
            match_type = "name_prefix"
        elif vcd_signal_name.endswith(signal_name):
            score += 35
            match_type = "name_suffix"
        elif signal_name.lower() in vcd_signal_name.lower():
            score += 25
            match_type = "name_contains"

        for part in path_parts[:-1]:
            if part == signal_name:
                score += 15
                match_type = "path_contains"
                break

        if instance_path:
            normalized_instance = instance_path.rstrip(".")
            vcd_prefix = ".".join(path_parts[:-1])

            if vcd_prefix == normalized_instance:
                score += 30
                match_type = "path_exact"
            elif vcd_prefix.startswith(normalized_instance + "."):
                score += 20
            elif normalized_instance in vcd_prefix:
                score += 15
            elif vcd_prefix in normalized_instance:
                score += 10

        for var_def in self._raw_var_definitions:
            if var_def["name"] == signal_name and vcd_path.endswith("." + signal_name):
                score += 5
                break

        return min(score, 100), match_type

    def _calculate_match_score(self, signal_name, vcd_path, instance_path=None):
        """
        计算信号匹配分数 (兼容旧版)

        Args:
            signal_name: 目标信号名
            vcd_path: VCD 信号路径
            instance_path: 实例路径 (可选)

        Returns:
            int: 匹配分数 (0-100)
        """
        score, _ = self._calculate_match_score_v2(signal_name, vcd_path, instance_path)
        return score

    def get_signal_timeline(self, vcd_signal_path, start_time=None, end_time=None):
        """
        获取信号变化时序

        Args:
            vcd_signal_path: VCD 信号路径
            start_time: 起始时间 (可选)
            end_time: 结束时间 (可选)

        Returns:
            list: [(time, value), ...]
        """
        if vcd_signal_path not in self._signals:
            raise ValueError(f"Signal not found: {vcd_signal_path}")

        signal_info = self._signals[vcd_signal_path]
        tv = signal_info["tv"]

        if start_time is not None or end_time is not None:
            filtered = []
            for t, v in tv:
                if start_time is not None and t < start_time:
                    continue
                if end_time is not None and t > end_time:
                    continue
                filtered.append((t, v))
            return filtered

        return list(tv)

    def get_signal_value_at_time(self, vcd_signal_path, time):
        """
        获取指定时刻的信号值

        Args:
            vcd_signal_path: VCD 信号路径
            time: 时间点

        Returns:
            str: 信号值
        """
        if vcd_signal_path not in self._signals:
            raise ValueError(f"Signal not found: {vcd_signal_path}")

        signal_info = self._signals[vcd_signal_path]
        signal_obj = signal_info["signal_obj"]

        return signal_obj[time]

    def get_signal_width(self, vcd_signal_path):
        """
        获取信号位宽

        Args:
            vcd_signal_path: VCD 信号路径

        Returns:
            int: 位宽
        """
        if vcd_signal_path not in self._signals:
            raise ValueError(f"Signal not found: {vcd_signal_path}")

        return self._signals[vcd_signal_path]["size"]

    def detect_anomalies(self, vcd_signal_path):
        """
        检测信号异常

        Args:
            vcd_signal_path: VCD 信号路径

        Returns:
            dict: 异常检测结果
        """
        if vcd_signal_path not in self._signals:
            raise ValueError(f"Signal not found: {vcd_signal_path}")

        signal_info = self._signals[vcd_signal_path]
        tv = signal_info["tv"]

        result = {
            "stuck_at_0": False,
            "stuck_at_1": False,
            "stuck_at_x": False,
            "stuck_at_z": False,
            "never_changed": False,
            "transitions": 0,
            "final_value": None,
            "initial_value": None,
            "all_values": [],
        }

        if not tv:
            result["never_changed"] = True
            return result

        result["initial_value"] = tv[0][1]
        result["final_value"] = tv[-1][1]
        result["transitions"] = len(tv) - 1

        for t, v in tv:
            if v not in result["all_values"]:
                result["all_values"].append(v)

        unique_values = set(result["all_values"])

        if len(unique_values) == 1:
            only_value = list(unique_values)[0]

            if only_value == "0":
                result["stuck_at_0"] = True
            elif only_value == "1":
                result["stuck_at_1"] = True
            elif "x" in only_value.lower():
                result["stuck_at_x"] = True
            elif "z" in only_value.lower():
                result["stuck_at_z"] = True

            result["never_changed"] = True

        return result

    def get_signal_summary(self, vcd_signal_path):
        """
        获取信号摘要信息

        Args:
            vcd_signal_path: VCD 信号路径

        Returns:
            dict: 信号摘要
        """
        if vcd_signal_path not in self._signals:
            raise ValueError(f"Signal not found: {vcd_signal_path}")

        signal_info = self._signals[vcd_signal_path]
        anomalies = self.detect_anomalies(vcd_signal_path)

        return {
            "vcd_path": vcd_signal_path,
            "width": signal_info["size"],
            "transitions": anomalies["transitions"],
            "initial_value": anomalies["initial_value"],
            "final_value": anomalies["final_value"],
            "all_values": list(anomalies["all_values"]),
            "anomalies": anomalies,
        }

    def build_signal_mapping_from_module(self, module_name, instance_path=""):
        """
        从模块信息构建信号映射

        利用 vtags 数据库的模块 IO 信息，生成信号名到 VCD 路径的映射

        Args:
            module_name: 模块名
            instance_path: 实例路径前缀

        Returns:
            dict: {signal_name: vcd_path}
        """
        if not self._G:
            return {}

        import Lib.FileInfLib as FileInfLib

        module_inf = FileInfLib.get_module_inf(module_name)
        if not module_inf:
            return {}

        mapping = {}
        prefix = instance_path + "." if instance_path else ""

        for io_inf in module_inf.get("io_inf_list", []):
            signal_name = io_inf["name_sr"]["str"]
            vcd_path = prefix + signal_name

            for vcd_signal in self._signals:
                if vcd_signal.endswith("." + signal_name):
                    parts = vcd_signal.split(".")
                    if len(parts) >= 2:
                        parent_path = ".".join(parts[:-1])
                        if instance_path and parent_path.startswith(instance_path):
                            mapping[signal_name] = vcd_signal
                            break
                        elif not instance_path:
                            mapping[signal_name] = vcd_signal

        return mapping

    def get_end_time(self):
        """获取 VCD 结束时间"""
        if not self._vcd:
            return None
        return self._vcd.endtime

    def get_signal_count(self):
        """获取信号总数"""
        return len(self._signals)
