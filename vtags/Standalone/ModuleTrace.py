"""
模块追踪、拓扑和文件列表功能
独立于 Vim 的实现
"""

import os
import re
import fnmatch
import Lib.FileInfLib as FileInfLib


class ModuleTrace:
    """
    模块追踪类，提供模块追踪、拓扑、文件列表等功能
    """

    def __init__(self, G):
        """
        初始化

        Args:
            G: 全局状态字典
        """
        self._G = G

    def get_trace(self, module_name):
        """
        获取模块调用追踪链

        从指定模块向上追踪到顶层模块

        Args:
            module_name: 模块名称

        Returns:
            list: 追踪链列表
        """
        full_traces = []
        FileInfLib.recursion_get_module_trace(module_name, [], full_traces)

        result = []
        for i, r_trace in enumerate(full_traces):
            trace = r_trace[::-1]
            father_inst_chain = trace[0]
            modules = []
            instances = []
            files = []

            for j, father_inst in enumerate(trace):
                parts = father_inst.split(".")
                modules.append(parts[0])
                if j > 0:
                    instances.append(parts[1] if len(parts) > 1 else "")
                father_inst_chain += "(%s).%s" % (
                    parts[0],
                    parts[1] if len(parts) > 1 else "",
                )

            father_inst_chain += "(%s)" % module_name
            modules.append(module_name)

            for mod in modules:
                mod_inf = FileInfLib.get_module_inf(mod)
                if mod_inf:
                    files.append(mod_inf.get("file_path", ""))
                else:
                    files.append("")

            result.append(
                {
                    "chain": father_inst_chain,
                    "modules": modules,
                    "instances": instances,
                    "files": files,
                }
            )

        return result

    def get_topo(self, module_name, depth=1, mask_threshold=None):
        """
        获取模块拓扑结构

        Args:
            module_name: 模块名称
            depth: 展开深度 (0=无限)
            mask_threshold: 实例数超过此值的模块将被折叠

        Returns:
            dict: 拓扑结构
        """
        if mask_threshold is None:
            mask_threshold = self._G.get("BaseModuleInf", {}).get(
                "BaseModuleThreshold", 200
            )

        base_modules = self._G.get("BaseModuleInf", {}).get("BaseModules", set())

        def _build_topo(mod_name, inst_name, cur_depth):
            mod_inf = FileInfLib.get_module_inf(mod_name)

            node = {
                "module": mod_name,
                "file": mod_inf.get("file_path", "") if mod_inf else "",
                "line": mod_inf["module_name_sr"]["range"][0]
                if mod_inf and "module_name_sr" in mod_inf
                else -1,
            }

            if inst_name:
                node["instance"] = inst_name
            else:
                node["instance"] = ""

            if depth != 0 and cur_depth >= depth:
                node["children"] = []
                node["folded"] = True
                return node

            if not mod_inf:
                node["children"] = []
                return node

            inst_list = mod_inf.get("inst_inf_list", [])

            if not inst_list:
                node["children"] = []
                return node

            instance_count = {}
            for inst_inf in inst_list:
                sub_mod = inst_inf["submodule_name_sr"]["str"]
                instance_count[sub_mod] = instance_count.get(sub_mod, 0) + 1

            children = []
            folded_children = []

            for inst_inf in inst_list:
                sub_mod = inst_inf["submodule_name_sr"]["str"]
                sub_inst = inst_inf["inst_name_sr"]["str"]

                if sub_mod in base_modules or (
                    mask_threshold > 0
                    and instance_count.get(sub_mod, 0) >= mask_threshold
                ):
                    if sub_mod not in [c["module"] for c in folded_children]:
                        folded_children.append(
                            {
                                "module": sub_mod,
                                "count": instance_count.get(sub_mod, 0),
                                "folded": True,
                            }
                        )
                else:
                    child = _build_topo(sub_mod, sub_inst, cur_depth + 1)
                    children.append(child)

            if folded_children:
                node["folded_modules"] = folded_children

            node["children"] = children

            return node

        return _build_topo(module_name, "", 0)

    def get_filelist(self, module_name):
        """
        获取模块及其子模块的所有文件列表

        Args:
            module_name: 模块名称

        Returns:
            list: 文件路径列表
        """
        trace_files = set()

        def _rec_get_files(mod_name):
            mod_inf = FileInfLib.get_module_inf(mod_name)
            if not mod_inf:
                return

            mod_path = mod_inf.get("file_path", "")
            if mod_path and (mod_name, mod_path) not in trace_files:
                trace_files.add((mod_name, mod_path))

            for inst_inf in mod_inf.get("inst_inf_list", []):
                sub_mod = inst_inf["submodule_name_sr"]["str"]
                _rec_get_files(sub_mod)

        _rec_get_files(module_name)

        return sorted(list(set([f[1] for f in trace_files])))

    def get_all_top_modules(self):
        """
        获取所有顶层模块列表

        Returns:
            list: 顶层模块名列表
        """
        return FileInfLib.get_all_top_modules()

    def get_module_info(self, module_name):
        """
        获取模块详细信息

        Args:
            module_name: 模块名称

        Returns:
            dict: 模块信息
        """
        mod_inf = FileInfLib.get_module_inf(module_name)

        if not mod_inf:
            return None

        ios = []
        for io_inf in mod_inf.get("io_inf_list", []):
            io_type = io_inf.get("type", 0)
            type_names = {0: "unknown", 1: "input", 2: "output", 3: "inout"}
            ios.append(
                {
                    "name": io_inf["name_sr"]["str"],
                    "type": type_names.get(io_type, "unknown"),
                    "width": io_inf.get("width", 1),
                    "line": io_inf["name_sr"]["range"][0],
                }
            )

        params = []
        for parm_inf in mod_inf.get("parm_inf_list", []):
            params.append(
                {
                    "name": parm_inf["str"],
                    "line": parm_inf["range"][0],
                }
            )

        instances = []
        for inst_inf in mod_inf.get("inst_inf_list", []):
            instances.append(
                {
                    "instance": inst_inf["inst_name_sr"]["str"],
                    "module": inst_inf["submodule_name_sr"]["str"],
                    "line": inst_inf["inst_name_sr"]["range"][0],
                }
            )

        return {
            "name": module_name,
            "file": mod_inf.get("file_path", ""),
            "line": mod_inf["module_name_sr"]["range"][0]
            if "module_name_sr" in mod_inf
            else -1,
            "ios": ios,
            "params": params,
            "instances": instances,
        }

    def search_module(self, pattern):
        """
        搜索匹配的模块名

        Args:
            pattern: 搜索模式 (支持通配符 * ?)

        Returns:
            list: 匹配的模块名列表
        """
        FileInfLib.onload_G_OffLineModulePathDic()
        all_modules_dic = FileInfLib.G.get("OffLineModulePathDic")
        if not all_modules_dic:
            all_modules_dic = self._G.get("OffLineModulePathDic", {})
        if not all_modules_dic:
            return []
        all_modules = all_modules_dic.keys()

        regex_pattern = fnmatch.translate(pattern)
        regex = re.compile(regex_pattern, re.IGNORECASE)

        return sorted([m for m in all_modules if regex.match(m)])

    def get_father_instances(self, module_name):
        """
        获取模块的所有父实例

        Args:
            module_name: 模块名称

        Returns:
            list: 父实例列表，每项格式为 'father_module.inst_name'
        """
        return FileInfLib.get_father_inst_list(module_name)

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
        topo = self.get_topo(module_name, depth)

        if format == "dot":
            return self._export_dot(topo)
        elif format == "json":
            return self._export_json(topo)
        elif format == "mermaid":
            return self._export_mermaid(topo)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_dot(self, topo):
        """导出 DOT 格式"""
        lines = [
            "digraph module_deps {",
            "    rankdir=TB;",
            "    node [shape=box, style=filled, fillcolor=lightblue];",
            "",
        ]

        nodes = []
        edges = []

        def collect_nodes_edges(node, parent=None):
            mod = node.get("module", "")
            file = node.get("file", "")
            inst = node.get("instance", "")

            filename = os.path.basename(file) if file else ""
            label = f"{mod}\\n{filename}" if filename else mod
            nodes.append((mod, f'    {mod} [label="{label}"];'))

            if parent:
                edge_label = inst if inst else ""
                edges.append(f'    {parent} -> {mod} [label="{edge_label}"];')

            for child in node.get("children", []):
                collect_nodes_edges(child, mod)

        collect_nodes_edges(topo)

        seen_mods = set()
        unique_nodes = []
        for mod, node_line in nodes:
            if mod not in seen_mods:
                seen_mods.add(mod)
                unique_nodes.append(node_line)

        unique_edges = list(dict.fromkeys(edges))

        lines.extend(unique_nodes)
        lines.append("")
        lines.extend(unique_edges)
        lines.append("}")

        return "\n".join(lines)

    def _export_mermaid(self, topo):
        """导出 Mermaid 格式"""
        lines = ["graph TD"]

        def collect_edges(node, parent=None):
            mod = node.get("module", "")
            inst = node.get("instance", "")

            if parent:
                label = f'["{inst}"]' if inst else ""
                lines.append(f"    {parent} -->{label} {mod}")

            for child in node.get("children", []):
                collect_edges(child, mod)

        collect_edges(topo)

        return "\n".join(lines)

    def _export_json(self, topo):
        """导出 JSON 格式"""
        import json

        return json.dumps(topo, indent=2)
