"""
信号追踪功能
独立于 Vim 的实现
"""

import os
import re
import copy
import Lib.GLB as GLB
import Lib.FileInfLib as FileInfLib
from Lib.BaseLib import search_verilog_code_use_grep, get_valid_code, get_sec_mtime


class SignalTrace:
    """
    信号追踪类，提供信号源和目的地追踪功能
    """

    def __init__(self, G):
        """
        初始化

        Args:
            G: 全局状态字典
        """
        self._G = G
        if G:
            GLB.G = G

    def trace(
        self,
        signal_name,
        file_path,
        line_num,
        column_num,
        trace_type,
        show_conditions=False,
    ):
        """
        追踪信号

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed)
            trace_type: 'source' 或 'dest'
            show_conditions: 是否显示条件信息

        Returns:
            dict: 追踪结果
        """
        if trace_type not in ["source", "dest"]:
            raise ValueError(
                f"trace_type must be 'source' or 'dest', got: {trace_type}"
            )

        file_path = os.path.realpath(file_path)

        if file_path in self._G.get("InLineIncFile2LogicFileDic", {}):
            logic_path = self._G["InLineIncFile2LogicFileDic"][file_path]
        else:
            logic_path = file_path

        module_io_inf = FileInfLib.get_module_io_inf_from_pos(
            file_path, (line_num, column_num)
        )
        io_inf = module_io_inf.get("io_inf")

        if io_inf:
            return self._trace_io_signal(
                signal_name,
                file_path,
                (line_num, column_num),
                module_io_inf,
                io_inf,
                trace_type,
            )

        module_inst_cnt_sub_inf = FileInfLib.get_module_inst_cnt_sub_inf_from_pos(
            file_path, (line_num, column_num)
        )
        inst_inf = module_inst_cnt_sub_inf.get("inst_inf")
        cnt_sub_inf = module_inst_cnt_sub_inf.get("cnt_sub_inf")

        if inst_inf and cnt_sub_inf:
            if trace_type == "source" and cnt_sub_inf["type"] == 1:
                pass
            elif trace_type == "dest" and cnt_sub_inf["type"] == 2:
                pass
            else:
                return self._trace_signal_at_subcall(
                    signal_name,
                    file_path,
                    (line_num, column_num),
                    module_inst_cnt_sub_inf,
                    trace_type,
                )

        return self._trace_normal_signal(
            signal_name,
            file_path,
            (line_num, column_num),
            module_io_inf.get("module_inf"),
            trace_type,
            show_conditions,
        )

    def _trace_io_signal(
        self, signal_name, file_path, pos, module_io_inf, io_inf, trace_type
    ):
        """
        追踪 IO 信号 (跨越模块边界)
        """
        result = {
            "signal_name": signal_name,
            "trace_type": trace_type,
            "sure": [],
            "maybe": [],
        }

        if trace_type == "dest" and io_inf["type"] == 1:
            return result
        if trace_type == "source" and io_inf["type"] == 2:
            return result

        cur_module_name = module_io_inf["module_inf"]["module_name_sr"]["str"]

        trace_father_inst = FileInfLib.track_module_trace(cur_module_name)
        father_inst_list = []

        if trace_father_inst:
            father_inst_list.append(trace_father_inst)
        else:
            father_inst_list = FileInfLib.get_father_inst_list(cur_module_name)

        if not father_inst_list:
            return result

        for father_inst in father_inst_list[:1]:
            father_module_name, inst_name = father_inst.split(".")
            father_inst_cnt_inf = FileInfLib.get_module_inst_iocnt_inf(
                father_module_name, inst_name, io_inf["name_sr"]["str"], io_inf["idx"]
            )

            iocnt_inf = father_inst_cnt_inf.get("iocnt_inf")
            if not iocnt_inf:
                continue

            father_module_inf = father_inst_cnt_inf["module_inf"]
            logic_cnt_name_range = iocnt_inf["cnt_name_range"]

            real_location = FileInfLib.location_l2r(
                logic_cnt_name_range, father_module_inf["code_inf_list"]
            )

            if not real_location:
                continue

            code_line = self._read_file_line(
                real_location["path"], real_location["pos"][0]
            )

            result["sure"].append(
                {
                    "file": real_location["path"],
                    "line": real_location["pos"][0],
                    "column": real_location["pos"][1],
                    "code": code_line,
                    "module": father_module_name,
                    "instance": inst_name,
                }
            )

        return result

    def _trace_signal_at_subcall(
        self, signal_name, file_path, pos, module_inst_cnt_sub_inf, trace_type
    ):
        """
        追踪子模块调用处的信号
        """
        result = {
            "signal_name": signal_name,
            "trace_type": trace_type,
            "sure": [],
            "maybe": [],
        }

        cnt_sub_inf = module_inst_cnt_sub_inf["cnt_sub_inf"]

        submodule_name = cnt_sub_inf["module_name_sr"]["str"]
        submodule_path = cnt_sub_inf["file_path"]
        subio_name = cnt_sub_inf["name_sr"]["str"]
        subio_range = cnt_sub_inf["name_sr"]["range"]

        subio_line = self._read_file_line(submodule_path, subio_range[0])

        real_location = FileInfLib.location_l2r(
            subio_range, cnt_sub_inf["module_inf"]["code_inf_list"]
        )

        if not real_location:
            return result

        result["sure"].append(
            {
                "file": real_location["path"],
                "line": real_location["pos"][0],
                "column": real_location["pos"][1],
                "code": subio_line,
                "module": submodule_name,
                "instance": "",
            }
        )

        return result

    def _trace_normal_signal(
        self, signal_name, file_path, pos, module_inf, trace_type, show_conditions=False
    ):
        """
        追踪模块内的普通信号
        """
        result = {
            "signal_name": signal_name,
            "trace_type": trace_type,
            "sure": [],
            "maybe": [],
        }

        if not module_inf:
            return result

        cur_module_name = module_inf["module_name_sr"]["str"]

        io_name_to_io_inf_map = {}
        for io_inf in module_inf.get("io_inf_list", []):
            io_name_to_io_inf_map[io_inf["name_sr"]["str"]] = io_inf
        module_inf["io_name_to_io_inf_map"] = io_name_to_io_inf_map

        if signal_name in io_name_to_io_inf_map:
            cur_io_inf = io_name_to_io_inf_map[signal_name]

            io_type = cur_io_inf["type"]
            is_only_result = False

            if (trace_type == "source" and io_type == 1) or (
                trace_type == "dest" and io_type == 2
            ):
                is_only_result = trace_type == "source"

                real_location = FileInfLib.location_l2r(
                    cur_io_inf["name_sr"]["range"], module_inf["code_inf_list"]
                )

                if real_location:
                    io_line = self._read_file_line(
                        real_location["path"], real_location["pos"][0]
                    )
                    result["sure"].append(
                        {
                            "file": real_location["path"],
                            "line": real_location["pos"][0],
                            "column": real_location["pos"][1],
                            "code": io_line,
                            "module": cur_module_name,
                            "instance": "",
                        }
                    )

            if is_only_result:
                return result

        path_range_map = {}
        line_boundry_map = {}

        for code_inf in module_inf.get("code_inf_list", []):
            c_path = code_inf["file_path"]
            if c_path not in path_range_map:
                path_range_map[c_path] = list(code_inf["real_line_range"])
                line_boundry_map[c_path] = [code_inf.get("real_code_line_boundry", [])]
            else:
                path_range_map[c_path][1] = code_inf["real_line_range"][1]
                line_boundry_map[c_path].append(
                    code_inf.get("real_code_line_boundry", [])
                )

        signal_appear_pos_line = []
        for path in path_range_map:
            signal_appear_pos_line += search_verilog_code_use_grep(
                signal_name, path, tuple(path_range_map[path])
            )

        for appear_path, appear_pos, appear_line in signal_appear_pos_line:
            valid_code = get_valid_code(appear_line)

            if re.search(r"(\W|^)(input|output|inout)(\W)", valid_code):
                continue

            module_inst_cnt_sub_inf = FileInfLib.get_module_inst_cnt_sub_inf_from_pos(
                appear_path, appear_pos
            )
            inst_inf = module_inst_cnt_sub_inf.get("inst_inf")

            appear_is_source = False
            appear_is_dest = False
            appear_dest_or_source = False
            submodule_and_subinstance = ""

            if inst_inf:
                submodule_and_subinstance = ":%s(%s)" % (
                    inst_inf["inst_name_sr"]["str"],
                    inst_inf["submodule_name_sr"]["str"],
                )
                cnt_sub_inf = module_inst_cnt_sub_inf.get("cnt_sub_inf")

                if not cnt_sub_inf:
                    appear_dest_or_source = True
                else:
                    io_type = cnt_sub_inf["type"]
                    if io_type != 1:
                        appear_is_source = True
                    if io_type != 2:
                        appear_is_dest = True
            else:
                code_line, new_y = self._get_code_logic_full_line(
                    appear_path, appear_pos, line_boundry_map.get(appear_path, [])
                )
                dest_or_source = self._current_appear_is_dest_or_source(
                    signal_name, (code_line, new_y)
                )

                if dest_or_source == "source":
                    appear_is_source = True
                elif dest_or_source == "dest":
                    appear_is_dest = True
                else:
                    appear_dest_or_source = True

            show_str = "%s %d : %s" % (
                cur_module_name + submodule_and_subinstance,
                appear_pos[0] + 1,
                appear_line,
            )

            trace_item = {
                "file": appear_path,
                "line": appear_pos[0],
                "column": appear_pos[1],
                "code": appear_line.rstrip("\n"),
                "module": cur_module_name,
                "instance": submodule_and_subinstance,
                "condition": None,
                "branch_type": None,
                "always_type": None,
            }

            if show_conditions and (appear_is_source or appear_is_dest):
                cond_info = self._extract_assignment_condition(
                    appear_path, appear_pos[0], signal_name
                )
                if cond_info:
                    trace_item["condition"] = cond_info.get("condition")
                    trace_item["branch_type"] = cond_info.get("branch_type")
                    trace_item["always_type"] = cond_info.get("always_type")

            if trace_type == "source":
                if appear_dest_or_source:
                    result["maybe"].append(trace_item)
                elif appear_is_source:
                    result["sure"].append(trace_item)
            else:
                if appear_dest_or_source:
                    result["maybe"].append(trace_item)
                elif appear_is_dest:
                    result["sure"].append(trace_item)

        return result

    def _current_appear_is_dest_or_source(self, key, code_y):
        """
        判断信号出现位置是源还是目的地

        Args:
            key: 信号名
            code_y: (代码行, 列号) 元组

        Returns:
            str: 'source', 'dest', 或 'unknown'
        """
        code_line, y = code_y

        if len(code_line) <= y or not re.match(
            r"\w", code_line[y] if y < len(code_line) else ""
        ):
            return "unknown"

        pure_line = self._replace_note_and_no_bracket_level_one_code(code_line)

        if len(pure_line) != len(code_line):
            pure_line = pure_line[: len(code_line)]

        if y < len(pure_line):
            if pure_line[y] == "/" or pure_line[y] == '"':
                return "unknown"

            if pure_line[y] == "(" and re.search(
                r"(\W|^)(if|case|casez|casex|for)\s*\(*", pure_line[:y]
            ):
                return "dest"

        pure_line_from_y = pure_line[y:] if y < len(pure_line) else ""
        pure_line_to_y = pure_line[:y]

        if re.search(r"(([^=>]|^)=([^=<]+|$)|<=)", pure_line_from_y):
            return "source"

        if re.search(r"(([^=]|^)=([^=]+|$)|<=)", pure_line_to_y):
            return "dest"

        return "unknown"

    def _replace_note_and_no_bracket_level_one_code(self, line):
        """
        预处理代码行：移除注释，标记字符串和括号

        Args:
            line: 代码行

        Returns:
            str: 处理后的代码行
        """
        pre_asterisk = 0
        pre_backslash = 0
        cur_backslash = 0
        cur_asterisk = 0
        in_single_line_notes = 0
        in_multi_line_notes = 0
        in_string = 0
        bracket_level = 0
        pure_line = ""

        for y, c in enumerate(line):
            cur_backslash = 0
            cur_asterisk = 0

            if c == "/":
                cur_backslash = 1
            elif c == "*":
                cur_asterisk = 1

            if not in_multi_line_notes and pre_backslash and cur_backslash:
                in_single_line_notes = 1
                pure_line += c
                continue

            if not in_single_line_notes and pre_backslash and cur_asterisk:
                in_multi_line_notes = 1
                pure_line += "/"
                continue

            if pre_asterisk and cur_backslash and in_multi_line_notes:
                in_multi_line_notes = 0
                pure_line += "/"
                continue

            if c == "\n" and in_single_line_notes:
                in_single_line_notes = 0
                pure_line += c
                continue

            pre_backslash = cur_backslash
            pre_asterisk = cur_asterisk

            if not (in_single_line_notes or in_multi_line_notes):
                if not in_string and c == '"':
                    in_string = 1
                elif in_string and c == '"':
                    in_string = 0

            if in_single_line_notes or in_multi_line_notes:
                pure_line += " "
            elif in_string:
                pure_line += '"'
            elif bracket_level != 0:
                pure_line += "("
            elif c == "\n":
                pure_line += "\\"
            else:
                pure_line += c

            if not (in_single_line_notes or in_multi_line_notes or in_string):
                if c == "(":
                    bracket_level += 1
                elif c == ")":
                    bracket_level -= 1
                    if bracket_level < 0:
                        bracket_level = 0

        return pure_line

    def _read_file_line(self, file_path, line_num):
        """
        读取文件指定行

        Args:
            file_path: 文件路径
            line_num: 行号 (0-indexed)

        Returns:
            str: 代码行
        """
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
                if 0 <= line_num < len(lines):
                    return lines[line_num].rstrip("\n")
        except:
            pass
        return ""

    def _get_code_logic_full_line(self, file_path, pos, line_boundry_list_list):
        """
        获取完整的逻辑代码行 (处理多行语句)

        Args:
            file_path: 文件路径
            pos: (行号, 列号)
            line_boundry_list_list: 行边界列表

        Returns:
            tuple: (完整代码行, 新列号)
        """
        x, y = pos

        try:
            with open(file_path, "r") as f:
                codes = f.readlines()
        except:
            return "", y

        line_range = [x, x]
        stop = 0

        for line_boundry_list in line_boundry_list_list:
            if stop:
                break
            for line_boundry in line_boundry_list:
                if stop:
                    break
                if not line_boundry or len(line_boundry) < 3:
                    continue

                line_start = line_boundry[0]
                line_offset = line_boundry[1]
                line_repeat_times = line_boundry[2]
                line_end = line_start - 1 + line_offset * line_repeat_times

                if line_end < x:
                    continue
                if line_start > x:
                    stop = 1
                    break

                for i in range(line_start, line_end + 1, line_offset):
                    if i <= x < i + line_offset:
                        line_range = [i, i + line_offset - 1]
                        stop = 1
                        break

        logic_lines = codes[line_range[0] : line_range[1] + 1]
        logic_line = "".join(logic_lines)

        new_y = 0
        for i, l in enumerate(logic_lines):
            if i < x - line_range[0]:
                new_y += len(l)
            elif i == x - line_range[0]:
                new_y += y
                break

        return logic_line, new_y

    def trace_macro_define(self, macro_name):
        """
        追踪宏定义

        Args:
            macro_name: 宏名称

        Returns:
            dict: 宏定义信息
        """
        result = {
            "signal_name": macro_name,
            "trace_type": "source",
            "sure": [],
            "maybe": [],
        }

        macro_inf = FileInfLib.get_macro_inf(macro_name)

        if not macro_inf:
            return result

        file_path = macro_inf["file_state"]["file_path"]
        line_num = macro_inf["name_sr"]["range"][0]
        code_line = self._read_file_line(file_path, line_num)

        result["sure"].append(
            {
                "file": file_path,
                "line": line_num,
                "column": macro_inf["name_sr"]["range"][1],
                "code": code_line,
                "module": "",
                "instance": "",
            }
        )

        return result

    def get_signal_full_paths(
        self, signal_name, file_path, line_num, column_num, trace_type, max_paths=5
    ):
        """
        获取信号的完整实例路径列表

        Args:
            signal_name: 信号名
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed)
            trace_type: 'source' 或 'dest'
            max_paths: 最大返回数量 (默认 5)

        Returns:
            dict: {
                "signal_name": "i_clk",
                "trace_type": "dest",
                "max_paths": 5,
                "paths": [...],
                "total_found": 12,
                "limited": True/False
            }
        """
        result = {
            "signal_name": signal_name,
            "trace_type": trace_type,
            "max_paths": max_paths,
            "paths": [],
            "total_found": 0,
            "limited": False,
        }

        trace_result = self.trace(
            signal_name, file_path, line_num, column_num, trace_type
        )

        sure_list = trace_result.get("sure", [])
        maybe_list = trace_result.get("maybe", [])

        all_items = sure_list + maybe_list

        all_paths = []
        seen_paths = set()

        for item in all_items:
            module = item.get("module", "")
            instance = item.get("instance", "")
            file = item.get("file", "")
            line = item.get("line", 0)
            code = item.get("code", "")

            full_path = self._build_full_instance_path(module, instance)

            if full_path in seen_paths:
                continue

            seen_paths.add(full_path)

            is_top_port = False
            if not instance and code:
                if re.search(r"^\s*(input|output)\s+", code):
                    father_list = FileInfLib.get_father_inst_list(module)
                    if not father_list:
                        is_top_port = True

            path_info = {
                "full_path": full_path,
                "module": module,
                "instance": instance,
                "file": file,
                "line": line,
                "code": code.strip() if code else "",
                "is_top_port": is_top_port,
            }
            all_paths.append(path_info)

        result["total_found"] = len(all_paths)

        if len(all_paths) > max_paths:
            result["paths"] = all_paths[:max_paths]
            result["limited"] = True
        else:
            result["paths"] = all_paths
            result["limited"] = False

        return result

    def _build_full_instance_path(self, module_name, instance_name=""):
        """
        构建从顶层到当前模块/实例的完整路径

        Args:
            module_name: 模块名
            instance_name: 实例名（可选）

        Returns:
            str: 完整实例路径，如 "switch_core_top.rx_mac_mng_inst"
        """
        path_parts = []

        if instance_name and ":" in instance_name:
            inst_match = re.match(r":(\w+)\((\w+)\)", instance_name)
            if inst_match:
                path_parts.append(inst_match.group(1))
        elif instance_name:
            path_parts.append(instance_name)

        current_module = module_name
        visited = set()
        top_module = None

        while current_module and current_module not in visited:
            visited.add(current_module)

            try:
                father_list = FileInfLib.get_father_inst_list(current_module)
            except (KeyError, Exception):
                father_list = None

            if not father_list:
                top_module = current_module
                break

            father_inst = father_list[0]
            parts = father_inst.split(".")
            if len(parts) == 2:
                father_module, inst_name = parts
                path_parts.insert(0, inst_name)
                current_module = father_module
            else:
                break

        if top_module:
            path_parts.insert(0, top_module)

        if path_parts:
            return ".".join(path_parts)

        return module_name

    def trace_recursive(
        self, signal_name, file_path, line_num, column_num, trace_type, max_depth=5
    ):
        """
        递归追踪信号

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed)
            trace_type: 'source' 或 'dest'
            max_depth: 最大追踪深度 (0=无限)

        Returns:
            dict: {
                "signal_name": "原始信号名",
                "trace_type": "source/dest",
                "max_depth": 最大深度,
                "chain": [主追踪链],
                "maybe_branches": [可能的分支],
                "terminated_reason": "终止原因",
                "circular_path": "循环路径" 或 None
            }
        """
        result = {
            "signal_name": signal_name,
            "trace_type": trace_type,
            "max_depth": max_depth if max_depth > 0 else 999,
            "chain": [],
            "maybe_branches": [],
            "terminated_reason": None,
            "circular_path": None,
        }

        visited = set()
        self._trace_recursive_impl(
            signal_name,
            file_path,
            line_num,
            column_num,
            trace_type,
            max_depth if max_depth > 0 else 999,
            0,
            visited,
            result,
            [],
        )

        return result

    def _trace_recursive_impl(
        self,
        signal_name,
        file_path,
        line_num,
        column_num,
        trace_type,
        max_depth,
        current_depth,
        visited,
        result,
        path_stack,
    ):
        """
        递归追踪实现

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号
            column_num: 列号
            trace_type: 追踪类型
            max_depth: 最大深度
            current_depth: 当前深度
            visited: 已访问信号集合
            result: 结果字典
            path_stack: 路径栈（用于循环检测）
        """
        visit_key = (signal_name, file_path, line_num)

        if visit_key in visited:
            result["terminated_reason"] = "circular"
            circular_path = " → ".join(path_stack + [signal_name])
            result["circular_path"] = circular_path
            return

        visited.add(visit_key)
        path_stack.append(signal_name)

        # 先检查是否是端口定义行（顶层端口检测）
        code_line = self._read_file_line(file_path, line_num)
        if code_line:
            port_match = re.search(r"^\s*(input|output|inout)\s+", code_line)
            if port_match:
                # 这是端口定义行，检查模块是否有父模块
                try:
                    module_io_inf = FileInfLib.get_module_inf_from_pos(
                        file_path, (line_num, 0)
                    )
                    if module_io_inf:
                        module_inf = module_io_inf.get("module_inf", {})
                        module_name = module_inf.get("module_name_sr", {}).get("str")
                        if module_name:
                            try:
                                father_list = FileInfLib.get_father_inst_list(
                                    module_name
                                )
                            except (KeyError, Exception):
                                father_list = None

                            if not father_list:
                                # 没有父模块，这是顶层端口
                                port_type = port_match.group(1)
                                chain_item = {
                                    "signal_name": signal_name,
                                    "file": file_path,
                                    "line": line_num,
                                    "column": column_num,
                                    "code": code_line.strip(),
                                    "module": module_name,
                                    "instance": "",
                                    "depth": current_depth,
                                    "is_final": True,
                                    "match_type": "port",
                                    "terminal_type": f"top_{port_type}",
                                }
                                result["chain"].append(chain_item)
                                result["terminated_reason"] = f"top_{port_type}"
                                path_stack.pop()
                                return
                except (KeyError, Exception):
                    pass

        trace_result = self.trace(
            signal_name, file_path, line_num, column_num, trace_type
        )

        sure_list = trace_result.get("sure", [])
        maybe_list = trace_result.get("maybe", [])

        if not sure_list and not maybe_list:
            fallback_item = self._fallback_trace_in_parent(
                signal_name, file_path, line_num, trace_type
            )

            if fallback_item:
                chain_item = {
                    "signal_name": signal_name,
                    "file": fallback_item["file"],
                    "line": fallback_item["line"],
                    "column": fallback_item.get("column", 0),
                    "code": fallback_item["code"],
                    "module": fallback_item["module"],
                    "instance": fallback_item["instance"],
                    "depth": current_depth,
                    "is_final": False,
                    "match_type": "fallback",
                    "terminal_type": None,
                }

                is_terminal, terminal_type = self._is_terminal_node(
                    fallback_item, trace_type
                )
                chain_item["is_final"] = is_terminal
                chain_item["terminal_type"] = terminal_type

                result["chain"].append(chain_item)

                if is_terminal:
                    result["terminated_reason"] = terminal_type
                elif current_depth + 1 < max_depth:
                    next_signal = fallback_item.get("connected_signal")
                    if next_signal:
                        # 即使 next_signal == signal_name 也要继续递归
                        # 因为它们在不同的文件/模块中
                        visit_key = (
                            next_signal,
                            fallback_item["file"],
                            fallback_item["line"],
                        )
                        if visit_key not in visited:
                            actual_pos = self._find_signal_position(
                                next_signal,
                                fallback_item["file"],
                                fallback_item.get("module"),
                            )
                            if actual_pos:
                                self._trace_recursive_impl(
                                    next_signal,
                                    fallback_item["file"],
                                    actual_pos["line"],
                                    actual_pos.get("column", 0),
                                    trace_type,
                                    max_depth,
                                    current_depth + 1,
                                    visited.copy(),
                                    result,
                                    path_stack.copy(),
                                )
                            else:
                                self._trace_recursive_impl(
                                    next_signal,
                                    fallback_item["file"],
                                    fallback_item["line"],
                                    0,
                                    trace_type,
                                    max_depth,
                                    current_depth + 1,
                                    visited.copy(),
                                    result,
                                    path_stack.copy(),
                                )

                path_stack.pop()
                return

            if current_depth == 0:
                result["terminated_reason"] = "no_source"
            path_stack.pop()
            return

        for idx, item in enumerate(sure_list):
            chain_item = {
                "signal_name": signal_name,
                "file": item.get("file", ""),
                "line": item.get("line", 0),
                "column": item.get("column", 0),
                "code": item.get("code", ""),
                "module": item.get("module", ""),
                "instance": item.get("instance", ""),
                "depth": current_depth,
                "is_final": False,
                "match_type": "sure",
                "terminal_type": None,
            }

            is_terminal, terminal_type = self._is_terminal_node(item, trace_type)
            chain_item["is_final"] = is_terminal
            chain_item["terminal_type"] = terminal_type

            if idx == 0:
                result["chain"].append(chain_item)
            else:
                result["maybe_branches"].append(
                    {"from_depth": current_depth, "chain": [chain_item]}
                )

            if is_terminal:
                if not result["terminated_reason"]:
                    result["terminated_reason"] = terminal_type
            elif current_depth + 1 < max_depth:
                next_signal = self._extract_next_signal(item, trace_type)
                if next_signal and next_signal != signal_name:
                    actual_pos = self._find_signal_position(
                        next_signal, item["file"], item.get("module")
                    )
                    if actual_pos:
                        self._trace_recursive_impl(
                            next_signal,
                            item["file"],
                            actual_pos["line"],
                            actual_pos["column"],
                            trace_type,
                            max_depth,
                            current_depth + 1,
                            visited.copy(),
                            result,
                            path_stack.copy(),
                        )
                    else:
                        self._trace_recursive_impl(
                            next_signal,
                            item["file"],
                            item["line"],
                            item["column"],
                            trace_type,
                            max_depth,
                            current_depth + 1,
                            visited.copy(),
                            result,
                            path_stack.copy(),
                        )

        for item in maybe_list:
            chain_item = {
                "signal_name": signal_name,
                "file": item.get("file", ""),
                "line": item.get("line", 0),
                "column": item.get("column", 0),
                "code": item.get("code", ""),
                "module": item.get("module", ""),
                "instance": item.get("instance", ""),
                "depth": current_depth,
                "is_final": False,
                "match_type": "maybe",
                "terminal_type": None,
            }

            is_terminal, terminal_type = self._is_terminal_node(item, trace_type)
            chain_item["is_final"] = is_terminal
            chain_item["terminal_type"] = terminal_type

            result["maybe_branches"].append(
                {"from_depth": current_depth, "chain": [chain_item]}
            )

            if not is_terminal and current_depth + 1 < max_depth:
                next_signal = self._extract_next_signal(item, trace_type)
                if next_signal and next_signal != signal_name:
                    actual_pos = self._find_signal_position(
                        next_signal, item["file"], item.get("module")
                    )
                    if actual_pos:
                        self._trace_recursive_impl(
                            next_signal,
                            item["file"],
                            actual_pos["line"],
                            actual_pos["column"],
                            trace_type,
                            max_depth,
                            current_depth + 1,
                            visited.copy(),
                            result,
                            path_stack.copy(),
                        )
                    else:
                        self._trace_recursive_impl(
                            next_signal,
                            item["file"],
                            item["line"],
                            item["column"],
                            trace_type,
                            max_depth,
                            current_depth + 1,
                            visited.copy(),
                            result,
                            path_stack.copy(),
                        )

        if not result["terminated_reason"]:
            if current_depth + 1 >= max_depth:
                result["terminated_reason"] = "max_depth"
            else:
                result["terminated_reason"] = "no_source"

        path_stack.pop()

    def _is_terminal_node(self, trace_item, trace_type):
        """
        判断是否为终止节点

        Args:
            trace_item: 追踪项
            trace_type: 追踪类型

        Returns:
            tuple: (is_terminal, terminal_type)
        """
        code = trace_item.get("code", "")
        module = trace_item.get("module", "")
        instance = trace_item.get("instance", "")

        is_const, const_type = self._is_constant_assignment(code)
        if is_const:
            return True, const_type

        is_top, top_type = self._is_top_level_port(trace_item, trace_type)
        if is_top:
            return True, top_type

        is_macro = self._is_macro_definition(code)
        if is_macro:
            return True, "macro"

        return False, None

    def _is_constant_assignment(self, code):
        """
        判断是否为常量赋值

        Args:
            code: 代码行

        Returns:
            tuple: (is_constant, constant_type)
        """
        if not code:
            return False, None

        patterns = [
            (r"=\s*(1'b[01xXzZ_]+)", "constant_binary"),
            (r"=\s*(2'b[01xXzZ_]+)", "constant_binary"),
            (r"=\s*(4'b[01xXzZ_]+)", "constant_binary"),
            (r"=\s*(8'b[01xXzZ_]+)", "constant_binary"),
            (r"=\s*(\d+'b[01xXzZ_]+)", "constant_binary"),
            (r"=\s*(\d+'h[0-9a-fA-FxXzZ_]+)", "constant_hex"),
            (r"=\s*(\d+'d[0-9xXzZ_]+)", "constant_decimal"),
            (r"=\s*(\d+'o[0-7xXzZ_]+)", "constant_octal"),
            (r"=\s*(1'o[01xXzZ])", "constant_octal"),
            (r"=\s*(\d+)\s*;", "constant_decimal"),
            (r"=\s*(\d+)\s*,", "constant_decimal"),
            (r"=\s*(\d+)\s*\)", "constant_decimal"),
            (r"=\s*0\s*;", "constant_zero"),
            (r"=\s*1\s*;", "constant_one"),
        ]

        for pattern, const_type in patterns:
            if re.search(pattern, code):
                return True, const_type

        return False, None

    def _is_top_level_port(self, trace_item, trace_type):
        """
        判断是否为顶层模块端口

        Args:
            trace_item: 追踪项
            trace_type: 追踪类型

        Returns:
            tuple: (is_top_port, port_type)
        """
        module = trace_item.get("module", "")
        instance = trace_item.get("instance", "")

        if not module:
            return False, None

        try:
            father_inst_list = FileInfLib.get_father_inst_list(module)
        except (KeyError, Exception):
            father_inst_list = None

        if not father_inst_list:
            code = trace_item.get("code", "")
            if re.search(r"^\s*(input|output)\s+", code):
                if trace_type == "source":
                    return True, "top_input"
                else:
                    return True, "top_output"

        return False, None

    def _is_macro_definition(self, code):
        """
        判断是否为宏定义

        Args:
            code: 代码行

        Returns:
            bool: 是否为宏定义
        """
        if not code:
            return False

        if re.search(r"^\s*`define\s+", code):
            return True

        if re.search(r"`\w+", code):
            return True

        return False

    def _extract_next_signal(self, trace_item, trace_type):
        """
        从追踪结果中提取下一级信号名

        Args:
            trace_item: 追踪项
            trace_type: 追踪类型

        Returns:
            str: 下一级信号名，或 None
        """
        code = trace_item.get("code", "")
        instance = trace_item.get("instance", "")

        if instance and ":" in instance:
            match = re.search(r"[\.:]\s*(\w+)\s*\(", code)
            if match:
                return match.group(1)

        if trace_type == "source":
            assign_match = re.search(r"=\s*(\w+)\s*[;,]", code)
            if assign_match:
                return assign_match.group(1)

            assign_match2 = re.search(r"assign\s+\w+\s*=\s*(\w+)", code)
            if assign_match2:
                return assign_match2.group(1)

            bit_match = re.search(r"=\s*(\w+)\s*\[", code)
            if bit_match:
                return bit_match.group(1)

            concat_match = re.search(r"=\s*\{\s*(\w+)", code)
            if concat_match:
                return concat_match.group(1)

            ternary_match = re.search(r"=\s*(\w+)\s*\?", code)
            if ternary_match:
                return ternary_match.group(1)

            port_match = re.search(r"\.\s*(\w+)\s*\(\s*(\w+)", code)
            if port_match:
                return port_match.group(2)

        else:
            port_match = re.search(r"\.\s*(\w+)\s*\(", code)
            if port_match:
                return port_match.group(1)

        return None

    def _find_signal_position(self, signal_name, file_path, module_name=None):
        """
        在目标文件中搜索信号的实际位置

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            module_name: 模块名 (可选，用于限定搜索范围)

        Returns:
            dict: {"line": 行号, "column": 列号, "code": 代码行} 或 None
        """
        if not os.path.isfile(file_path):
            return None

        signal_appear_pos_line = search_verilog_code_use_grep(
            signal_name, file_path, (0, 999999)
        )

        if not signal_appear_pos_line:
            return None

        for appear_path, appear_pos, appear_line in signal_appear_pos_line:
            valid_code = get_valid_code(appear_line)

            if re.search(r"(\W|^)(input|output|inout)(\W)", valid_code):
                continue

            module_io_inf = FileInfLib.get_module_io_inf_from_pos(
                appear_path, appear_pos
            )
            io_inf = module_io_inf.get("io_inf")

            if io_inf:
                return {
                    "line": appear_pos[0],
                    "column": appear_pos[1],
                    "code": appear_line,
                    "is_io": True,
                }

            code_line, new_y = self._get_code_logic_full_line(
                appear_path, appear_pos, []
            )
            dest_or_source = self._current_appear_is_dest_or_source(
                signal_name, (code_line, new_y)
            )

            if dest_or_source in ["source", "dest"]:
                return {
                    "line": appear_pos[0],
                    "column": appear_pos[1],
                    "code": appear_line,
                    "is_io": False,
                }

        if signal_appear_pos_line:
            appear_path, appear_pos, appear_line = signal_appear_pos_line[0]
            return {
                "line": appear_pos[0],
                "column": appear_pos[1],
                "code": appear_line,
                "is_io": False,
            }

        return None

    def _fallback_trace_in_parent(self, signal_name, file_path, line_num, trace_type):
        """
        当正常追踪失败时，尝试在父模块实例化处搜索信号连接

        场景: 信号是模块的 input/output 端口，但由于 ifdef 等原因未被数据库识别

        Args:
            signal_name: 信号名
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            trace_type: 'source' 或 'dest'

        Returns:
            dict: 追踪结果项，或 None
        """
        try:
            module_io_inf = FileInfLib.get_module_inf_from_pos(file_path, (line_num, 0))
            if not module_io_inf:
                module_io_inf = FileInfLib.get_module_inf_from_pos(file_path, (0, 0))

            if module_io_inf:
                module_inf = module_io_inf.get("module_inf", {})
            else:
                module_inf = None

            if not module_inf:
                return None

            module_name = module_inf.get("module_name_sr", {}).get("str")
            if not module_name:
                return None

            father_list = FileInfLib.get_father_inst_list(module_name)
            if not father_list:
                return None

            for father_inst in father_list[:1]:
                parts = father_inst.split(".")
                if len(parts) != 2:
                    continue

                father_module, inst_name = parts

                father_module_inf = FileInfLib.get_module_inf(father_module)
                if not father_module_inf:
                    continue

                father_file = father_module_inf.get("file_path", "")
                if not father_file:
                    continue

                try:
                    with open(father_file, "r", errors="ignore") as f:
                        lines = f.readlines()
                except:
                    continue

                for line_idx, line in enumerate(lines):
                    pattern = rf"\.\s*{re.escape(signal_name)}\s*\(\s*(\w+)"
                    match = re.search(pattern, line)
                    if match:
                        connected_signal = match.group(1)
                        return {
                            "file": father_file,
                            "line": line_idx,
                            "column": 0,
                            "code": line.strip(),
                            "module": father_module,
                            "instance": inst_name,
                            "connected_signal": connected_signal,
                        }

        except Exception:
            pass

        return None

    def _extract_assignment_condition(self, file_path, line_num, signal_name=None):
        """
        提取赋值语句的条件信息（支持 if/elsif/else, 嵌套if, case, 三目运算符）

        Args:
            file_path: 文件路径
            line_num: 赋值语句行号 (0-indexed)
            signal_name: 信号名（用于三目运算符匹配）

        Returns:
            dict: {
                "condition": "swlist_vld && broadcast",
                "branch_type": "if/elsif/else/case/case_default/ternary",
                "always_type": "comb/seq/latch/assign",
                "conditions": [...]  # 嵌套条件列表
            } 或 None
        """
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
        except Exception:
            return None

        if line_num >= len(lines):
            return None

        code_line = lines[line_num].strip()

        # 1. 检查是否是 assign 语句（三目运算符）
        if signal_name and re.search(r"\bassign\b", code_line):
            ternary_info = self._extract_ternary_condition(code_line, signal_name)
            if ternary_info:
                ternary_info["always_type"] = "assign"
                return ternary_info

        # 2. 检查 case 语句
        case_line = self._find_case_block(lines, line_num)
        if case_line is not None:
            case_info = self._parse_case_branches(lines, case_line, line_num)
            if case_info:
                always_info = self._find_always_block(lines, case_line)
                case_info["always_type"] = always_info[1] if always_info else "comb"
                return case_info

        # 3. 检查 always 块（嵌套 if）
        always_info = self._find_always_block(lines, line_num)
        if always_info:
            always_line, always_type = always_info
            condition_info = self._parse_nested_conditions(lines, always_line, line_num)
            if condition_info:
                condition_info["always_type"] = always_type
                return condition_info

        return None

    def _remove_comments(self, line):
        """移除行内注释"""
        # 移除 // 注释
        line = re.sub(r"//.*$", "", line)
        # 移除 /* */ 注释
        line = re.sub(r"/\*.*?\*/", "", line)
        return line.strip()

    def _simplify_condition(self, condition):
        """简化条件表达式"""
        if not condition:
            return condition

        # 移除换行和多余空格
        condition = re.sub(r"\s+", " ", condition.strip())

        return condition

    def _find_always_block(self, lines, line_num):
        """
        向上扫描找到 always 块

        Returns:
            tuple: (always_line, always_type) 或 None
        """
        always_patterns = [
            (r"always\s*@\s*\(", "seq"),
            (r"always_comb\b", "comb"),
            (r"always_ff\s*@\s*\(", "seq"),
            (r"always_latch\b", "latch"),
        ]

        for i in range(line_num, -1, -1):
            line = lines[i].strip()
            code = self._remove_comments(line)

            if not code:
                continue

            for pattern, atype in always_patterns:
                if re.search(pattern, code):
                    return (i, atype)

            if re.search(r"\b(module|function|task|assign)\b", code):
                break

        return None

    def _find_case_block(self, lines, line_num):
        """
        向上扫描找到 case 块

        Returns:
            int: case 块起始行号，或 None
        """
        for i in range(line_num, -1, -1):
            line = lines[i].strip()
            code = self._remove_comments(line)

            if re.search(r"\bcase\s*\(", code):
                return i

            if re.search(r"\b(always|module|function|task)\b", code):
                break

        return None

    def _extract_ternary_condition(self, code_line, signal_name):
        """
        从三目运算符中提取条件
        """
        pattern = r"assign\s+" + re.escape(signal_name) + r"\s*=\s*(.+?)\s*\?"
        match = re.search(pattern, code_line)

        if not match:
            return None

        condition = match.group(1).strip()

        ternary_pattern = (
            r"assign\s+"
            + re.escape(signal_name)
            + r"\s*=\s*(.+?)\s*\?\s*(.+?)\s*:\s*(.+?)\s*;"
        )
        ternary_match = re.search(ternary_pattern, code_line)

        if ternary_match:
            return {
                "condition": self._simplify_condition(condition),
                "true_value": ternary_match.group(2).strip(),
                "false_value": ternary_match.group(3).strip(),
                "branch_type": "ternary",
            }

        return {
            "condition": self._simplify_condition(condition),
            "branch_type": "ternary",
        }

    def _parse_case_branches(self, lines, case_line, target_line):
        """
        解析 case 语句分支
        """
        case_match = re.search(r"case\s*\((.*?)\)\s*$", lines[case_line].strip())
        if not case_match:
            case_match = re.search(r"case\s*\((.*?)\)", lines[case_line].strip())

        if not case_match:
            return None

        case_expr = case_match.group(1).strip()

        i = case_line + 1
        current_branch = None
        branch_start = None
        begin_count = 0
        in_branch = False

        while i < len(lines):
            line = lines[i].strip()
            code = self._remove_comments(line)

            if re.search(r"\bendcase\b", code):
                break

            case_branch_match = re.search(r"(.*?)\s*:\s*begin\b", code)
            if case_branch_match:
                branch_value = case_branch_match.group(1).strip()
                current_branch = branch_value
                branch_start = i
                begin_count = 1
                in_branch = True
            else:
                default_match = re.search(r"default\s*:\s*begin\b", code)
                if default_match:
                    current_branch = "default"
                    branch_start = i
                    begin_count = 1
                    in_branch = True

            if in_branch:
                begin_count += len(re.findall(r"\bbegin\b", code))
                begin_count -= len(re.findall(r"\bend\b", code))

                if begin_count <= 0:
                    in_branch = False
                    current_branch = None

            if branch_start is not None and branch_start <= target_line <= i:
                if current_branch:
                    if current_branch == "default":
                        return {
                            "condition": f"{case_expr} == default",
                            "branch_type": "case_default",
                            "case_expr": case_expr,
                        }
                    else:
                        return {
                            "condition": f"{case_expr} == {current_branch}",
                            "branch_type": "case",
                            "case_expr": case_expr,
                            "case_value": current_branch,
                        }

            i += 1

        return None

    def _parse_nested_conditions(self, lines, always_line, target_line):
        """
        解析嵌套 if 语句，返回完整条件路径
        """
        condition_stack = []
        current_nest_level = 0

        i = always_line
        while i < len(lines):
            line = lines[i].strip()
            code = self._remove_comments(line)

            if_match = re.search(r"if\s*\((.*?)\)\s*begin\b", code)
            if if_match:
                condition = self._simplify_condition(if_match.group(1))
                condition_stack.append(
                    {
                        "condition": condition,
                        "branch_type": "if",
                        "nest_level": current_nest_level,
                        "start_line": i,
                    }
                )
                current_nest_level += 1

            elsif_match = re.search(r"else\s+if\s*\((.*?)\)\s*begin\b", code)
            if elsif_match:
                while (
                    condition_stack
                    and condition_stack[-1].get("nest_level", 0) >= current_nest_level
                ):
                    condition_stack.pop()

                condition = self._simplify_condition(elsif_match.group(1))
                condition_stack.append(
                    {
                        "condition": condition,
                        "branch_type": "elsif",
                        "nest_level": current_nest_level - 1
                        if current_nest_level > 0
                        else 0,
                        "start_line": i,
                    }
                )

            elif re.search(r"else\s+begin\b", code):
                while (
                    condition_stack
                    and condition_stack[-1].get("nest_level", 0) >= current_nest_level
                ):
                    condition_stack.pop()

                condition_stack.append(
                    {
                        "condition": "else",
                        "branch_type": "else",
                        "nest_level": current_nest_level - 1
                        if current_nest_level > 0
                        else 0,
                        "start_line": i,
                    }
                )

            end_count = len(re.findall(r"\bend\b", code))
            begin_count = len(re.findall(r"\bbegin\b", code))

            net_end = end_count - begin_count
            for _ in range(net_end):
                if current_nest_level > 0:
                    current_nest_level -= 1

            if i == target_line:
                return self._build_nested_condition(condition_stack)

            i += 1

        return None

    def _build_nested_condition(self, condition_stack):
        """
        从条件栈构建完整条件路径
        """
        if not condition_stack:
            return None

        valid_conditions = []
        for cond in condition_stack:
            btype = cond.get("branch_type", "if")
            condition = cond.get("condition", "")
            level = cond.get("nest_level", 0)

            if btype == "else":
                valid_conditions = [c for c in valid_conditions if c[2] < level]
                valid_conditions.append((condition, btype, level))
            else:
                valid_conditions = [c for c in valid_conditions if c[2] < level]
                valid_conditions.append((condition, btype, level))

        condition_parts = []
        branch_type = "if"

        for cond, btype, level in valid_conditions:
            if cond != "else":
                condition_parts.append(cond)
            branch_type = btype

        full_condition = " && ".join(condition_parts) if condition_parts else "else"

        if full_condition == "else":
            return {
                "condition": "else",
                "branch_type": "else",
                "conditions": [],
            }

        return {
            "condition": full_condition,
            "branch_type": branch_type,
            "conditions": [(c, t) for c, t, l in valid_conditions if c != "else"],
        }
