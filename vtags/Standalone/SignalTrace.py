"""
信号追踪功能
独立于 Vim 的实现
"""

import os
import re
import copy
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

    def trace(self, signal_name, file_path, line_num, column_num, trace_type):
        """
        追踪信号

        Args:
            signal_name: 信号名称
            file_path: 文件路径
            line_num: 行号 (0-indexed)
            column_num: 列号 (0-indexed)
            trace_type: 'source' 或 'dest'

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

    def _trace_normal_signal(self, signal_name, file_path, pos, module_inf, trace_type):
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
            }

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
