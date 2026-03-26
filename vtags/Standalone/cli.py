#!/usr/bin/env python3
"""
vtags 命令行工具
独立于 Vim 的命令行接口

用法:
    vtags-cli -db /path/to/vtags.db <command> [options]

命令:
    trace <module>              显示模块调用追踪链
    topo <module> [depth]       显示模块拓扑结构
    files <module>              显示模块文件列表
    tops                        列出所有顶层模块
    info <module>               显示模块详细信息
    search <pattern>            搜索匹配的模块

    strace <signal> <file> <line> [column]   追踪信号源
    dtrace <signal> <file> <line> [column]   追踪信号目的地

    vcd <vcd_file> [--list] [--signal NAME] [--file PATH --line NUM]
                                VCD 波形分析

选项:
    -db PATH      指定 vtags.db 路径
    -j, --json    JSON 格式输出
    -h, --help    显示帮助信息
"""

import argparse
import json
import os
import sys


def find_vtags_db(start_path=None):
    """从当前目录向上搜索 vtags.db"""
    if start_path is None:
        start_path = os.getcwd()

    cur_path = start_path
    level = 3

    while cur_path and cur_path[0] == "/":
        db_path = os.path.join(cur_path, "vtags.db")
        if os.path.isdir(db_path):
            return db_path
        cur_path = os.path.dirname(cur_path)
        level -= 1
        if level <= 0:
            break

    return None


def print_module_trace(traces, use_json=False):
    """打印模块追踪结果"""
    if use_json:
        print(json.dumps(traces, indent=2))
        return

    if not traces:
        print("No trace found.")
        return

    for i, trace in enumerate(traces):
        print(f"{i}: {trace['chain']}")


def print_module_topo(topo, use_json=False, indent=0):
    """打印模块拓扑"""
    if use_json:
        if indent == 0:
            print(json.dumps(topo, indent=2))
        return

    prefix = "    " * indent

    inst_str = (
        f"{topo.get('instance', '')}({topo['module']})"
        if topo.get("instance")
        else topo["module"]
    )
    print(f"{prefix}{inst_str}")

    if topo.get("folded"):
        print(f"{prefix}    ... (folded)")
        return

    for child in topo.get("children", []):
        print_module_topo(child, use_json, indent + 1)

    for folded in topo.get("folded_modules", []):
        print(f"{prefix}    {folded['module']}({folded['count']})  [folded]")


def print_signal_trace(result, use_json=False):
    """打印信号追踪结果"""
    if use_json:
        print(json.dumps(result, indent=2))
        return

    signal_name = result.get("signal_name", "")
    trace_type = result.get("trace_type", "")

    print(f"\n{'=' * 60}")
    print(f"Signal: {signal_name}")
    print(f"Trace Type: {trace_type}")
    print(f"{'=' * 60}")

    sure_list = result.get("sure", [])
    maybe_list = result.get("maybe", [])

    has_conditions = any(item.get("condition") for item in sure_list + maybe_list)

    if sure_list:
        print(f"\nSure {trace_type}:")
        for item in sure_list:
            line_num = int(item["line"]) + 1 if item.get("line") is not None else 0
            condition = item.get("condition")
            branch_type = item.get("branch_type")

            cond_str = ""
            if condition:
                if branch_type == "else":
                    cond_str = " [else branch]"
                elif branch_type == "ternary":
                    cond_str = f" [ternary: {condition}]"
                elif branch_type in ["case", "case_default"]:
                    cond_str = f" [case: {condition}]"
                else:
                    cond_str = f" [condition: {condition}]"

            print(
                f"  {item['module']}{item['instance']} {item['file']}:{line_num}{cond_str}"
            )
            print(f"    {item['code']}")

    if maybe_list:
        print(f"\nMaybe {trace_type}:")
        for item in maybe_list:
            line_num = int(item["line"]) + 1 if item.get("line") is not None else 0
            condition = item.get("condition")
            branch_type = item.get("branch_type")

            cond_str = ""
            if condition:
                if branch_type == "else":
                    cond_str = " [else branch]"
                elif branch_type == "ternary":
                    cond_str = f" [ternary: {condition}]"
                elif branch_type in ["case", "case_default"]:
                    cond_str = f" [case: {condition}]"
                else:
                    cond_str = f" [condition: {condition}]"

            print(
                f"  {item['module']}{item['instance']} {item['file']}:{line_num}{cond_str}"
            )
            print(f"    {item['code']}")

    if not sure_list and not maybe_list:
        print(f"\nNo {trace_type} found.")


def print_recursive_trace(result, use_json=False):
    """打印递归追踪结果"""
    if use_json:
        print(json.dumps(result, indent=2))
        return

    signal_name = result.get("signal_name", "")
    trace_type = result.get("trace_type", "")
    max_depth = result.get("max_depth", 0)
    chain = result.get("chain", [])
    maybe_branches = result.get("maybe_branches", [])
    terminated_reason = result.get("terminated_reason", "")
    circular_path = result.get("circular_path")

    print(f"\n{'=' * 60}")
    print(f"Signal: {signal_name}")
    print(f"Trace Type: {trace_type} (recursive, max_depth={max_depth})")
    print(f"{'=' * 60}")

    if circular_path:
        print(f"\n⚠️  CIRCULAR REFERENCE DETECTED:")
        print(f"  Path: {circular_path}")
        print(f"  Cannot trace further to avoid infinite loop")

    if chain:
        print(f"\nChain ({len(chain)} levels):")
        for item in chain:
            depth = item.get("depth", 0)
            sig_name = item.get("signal_name", "")
            file_path = item.get("file", "")
            line_num = int(item.get("line", 0)) + 1
            code = item.get("code", "").strip()
            module = item.get("module", "")
            instance = item.get("instance", "")
            match_type = item.get("match_type", "")
            is_final = item.get("is_final", False)
            terminal_type = item.get("terminal_type")

            indent = "  " * (depth + 1)
            arrow = "← " if depth > 0 else ""

            location = f"{file_path}:{line_num}" if file_path else "N/A"
            match_str = f" [{match_type}]" if match_type else ""
            terminal_str = f" [TERMINAL - {terminal_type.upper()}]" if is_final else ""

            print(
                f"{indent}[{depth}] {arrow}{sig_name} ({location}){match_str}{terminal_str}"
            )
            if code:
                print(f"{indent}      {code[:80]}")

    if maybe_branches:
        print(f"\nMaybe branches:")
        for branch in maybe_branches:
            from_depth = branch.get("from_depth", 0)
            branch_chain = branch.get("chain", [])
            for item in branch_chain:
                depth = item.get("depth", 0)
                sig_name = item.get("signal_name", "")
                file_path = item.get("file", "")
                line_num = int(item.get("line", 0)) + 1
                code = item.get("code", "").strip()

                indent = "  " * (depth + 1)
                print(
                    f"{indent}[{depth}.{from_depth}] ← {sig_name} ({file_path}:{line_num}) [maybe]"
                )
                if code:
                    print(f"{indent}        {code[:80]}")

    if terminated_reason:
        reason_map = {
            "constant": "constant assignment",
            "constant_binary": "binary constant assignment",
            "constant_hex": "hex constant assignment",
            "constant_decimal": "decimal constant assignment",
            "constant_zero": "constant zero",
            "constant_one": "constant one",
            "top_input": "top-level input port",
            "top_output": "top-level output port",
            "macro": "macro definition",
            "max_depth": "reached max depth",
            "no_source": "no source found",
            "circular": "circular reference",
        }
        reason_str = reason_map.get(terminated_reason, terminated_reason)
        print(f"\nTerminated: {reason_str}")

    if not chain and not maybe_branches:
        print(f"\nNo trace found.")


def print_vcd_list(signals, use_json=False):
    """打印 VCD 信号列表"""
    if use_json:
        print(json.dumps(signals, indent=2))
        return

    if not signals:
        print("No signals found.")
        return

    print(f"\nVCD Signals ({len(signals)}):")
    for i, sig in enumerate(signals):
        print(f"  {i}: {sig}")


def print_vcd_analysis(result, use_json=False, max_timeline=20):
    """打印 VCD 分析结果"""
    if use_json:
        print(json.dumps(result, indent=2))
        return

    signal_name = result.get("signal_name", "")
    vcd_path = result.get("vcd_path")
    instance_path = result.get("instance_path", "")

    print(f"\n{'=' * 60}")
    print(f"Signal: {signal_name}")
    if instance_path:
        print(f"Instance Path: {instance_path}")
    print(f"{'=' * 60}")

    if not vcd_path:
        matched = result.get("matched_signals", [])
        if matched:
            print("\nSignal not found. Similar signals:")
            for m in matched[:10]:
                print(f"  {m['vcd_path']} (score: {m['score']})")
        else:
            print("\nSignal not found in VCD file.")
        return

    print(f"\nVCD Path: {vcd_path}")
    print(f"Width: {result.get('width', '?')} bit(s)")

    timeline = result.get("timeline", [])
    if timeline:
        print(f"\nTimeline ({len(timeline)} transitions):")
        display_count = min(len(timeline), max_timeline)
        for time, value in timeline[:display_count]:
            print(f"  #{time}: {value}")
        if len(timeline) > max_timeline:
            print(f"  ... ({len(timeline) - max_timeline} more)")
    else:
        print("\nNo transitions recorded.")

    anomalies = result.get("anomalies", {})
    if anomalies:
        warnings = []
        if anomalies.get("stuck_at_0"):
            warnings.append("Signal stuck at 0")
        if anomalies.get("stuck_at_1"):
            warnings.append("Signal stuck at 1")
        if anomalies.get("stuck_at_x"):
            warnings.append("Signal stuck at X (unknown)")
        if anomalies.get("stuck_at_z"):
            warnings.append("Signal stuck at Z (high-impedance)")

        if warnings:
            print(f"\nWarnings:")
            for w in warnings:
                print(f"  [!] {w} - check driver logic")
        else:
            print(f"\nTransitions: {anomalies.get('transitions', 0)}")
            print(f"Initial value: {anomalies.get('initial_value', '?')}")
            print(f"Final value: {anomalies.get('final_value', '?')}")


def print_full_paths(result, use_json=False):
    """打印完整实例路径"""
    if use_json:
        print(json.dumps(result, indent=2))
        return

    signal_name = result.get("signal_name", "")
    trace_type = result.get("trace_type", "")
    paths = result.get("paths", [])
    total_found = result.get("total_found", 0)
    limited = result.get("limited", False)
    max_paths = result.get("max_paths", 5)

    print(f"\n{'=' * 60}")
    print(f"Signal: {signal_name}")
    print(f"Trace Type: {trace_type} (--full-path)")
    print(f"{'=' * 60}")

    if not paths:
        print(f"\nNo instance paths found.")
        return

    displayed = len(paths)
    if limited:
        print(
            f"\nFull Instance Paths ({displayed} of {total_found}, limited to {max_paths}):"
        )
    else:
        print(f"\nFull Instance Paths ({displayed}):")

    for i, path_info in enumerate(paths):
        full_path = path_info.get("full_path", "")
        file_path = path_info.get("file", "")
        line_num = path_info.get("line", 0) + 1
        code = path_info.get("code", "").strip()
        is_top_port = path_info.get("is_top_port", False)

        top_port_str = " [TOP PORT]" if is_top_port else ""
        print(f"  [{i}] {full_path}{top_port_str}")
        if file_path:
            print(f"        {file_path}:{line_num}")
        if code:
            print(f"        {code[:70]}")

    if limited:
        print(
            f"\n  ... {total_found - displayed} more paths not shown (use --full-path {total_found} to see all)"
        )


def main():
    parser = argparse.ArgumentParser(
        description="vtags standalone command line tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -db ./vtags.db trace cpu_top
  %(prog)s topo cpu_top 2
  %(prog)s -j files cpu_top
  %(prog)s strace clk rtl/cpu.v 42
  %(prog)s dtrace data_out rtl/cpu.v 100 5
        """,
    )

    parser.add_argument(
        "-db", "--database", dest="db_path", help="Path to vtags.db directory"
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="Output in JSON format"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    parser_trace = subparsers.add_parser("trace", help="Show module trace")
    parser_trace.add_argument("module", help="Module name")

    parser_topo = subparsers.add_parser("topo", help="Show module topology")
    parser_topo.add_argument("module", help="Module name")
    parser_topo.add_argument(
        "depth",
        nargs="?",
        type=int,
        default=1,
        help="Depth to expand (0 for unlimited)",
    )

    parser_files = subparsers.add_parser("files", help="Show module file list")
    parser_files.add_argument("module", help="Module name")

    parser_tops = subparsers.add_parser("tops", help="List all top modules")

    parser_info = subparsers.add_parser("info", help="Show module info")
    parser_info.add_argument("module", help="Module name")

    parser_search = subparsers.add_parser("search", help="Search modules")
    parser_search.add_argument("pattern", help="Search pattern (supports wildcards)")

    parser_strace = subparsers.add_parser("strace", help="Trace signal source")
    parser_strace.add_argument("signal", help="Signal name")
    parser_strace.add_argument("file", help="File path")
    parser_strace.add_argument("line", type=int, help="Line number (1-indexed)")
    parser_strace.add_argument(
        "column", nargs="?", type=int, default=0, help="Column number (0-indexed)"
    )
    parser_strace.add_argument(
        "-r",
        "--recursive",
        type=int,
        default=1,
        help="Recursive trace depth (0=unlimited, 1=single hop, default=1)",
    )
    parser_strace.add_argument(
        "--full-path",
        nargs="?",
        type=int,
        const=5,
        default=None,
        help="Show full instance paths (default: 5)",
    )
    parser_strace.add_argument(
        "--show-conditions",
        action="store_true",
        help="Show assignment conditions in always blocks",
    )

    parser_dtrace = subparsers.add_parser("dtrace", help="Trace signal destination")
    parser_dtrace.add_argument("signal", help="Signal name")
    parser_dtrace.add_argument("file", help="File path")
    parser_dtrace.add_argument("line", type=int, help="Line number (1-indexed)")
    parser_dtrace.add_argument(
        "column", nargs="?", type=int, default=0, help="Column number (0-indexed)"
    )
    parser_dtrace.add_argument(
        "-r",
        "--recursive",
        type=int,
        default=1,
        help="Recursive trace depth (0=unlimited, 1=single hop, default=1)",
    )
    parser_dtrace.add_argument(
        "--full-path",
        nargs="?",
        type=int,
        const=5,
        default=None,
        help="Show full instance paths (default: 5)",
    )
    parser_dtrace.add_argument(
        "--show-conditions",
        action="store_true",
        help="Show assignment conditions in always blocks",
    )

    parser_vcd = subparsers.add_parser("vcd", help="Analyze VCD waveform file")
    parser_vcd.add_argument("vcd_file", help="VCD file path")
    parser_vcd.add_argument(
        "--list", action="store_true", help="List all signals in VCD"
    )
    parser_vcd.add_argument(
        "--pattern", help="Filter signals by pattern (use with --list)"
    )
    parser_vcd.add_argument("--signal", help="Signal name to analyze")
    parser_vcd.add_argument("--file", help="Verilog file path (for instance context)")
    parser_vcd.add_argument("--line", type=int, help="Line number in Verilog file")
    parser_vcd.add_argument(
        "--max-timeline", type=int, default=20, help="Max timeline entries to display"
    )

    parser_export = subparsers.add_parser(
        "export-deps", help="Export module dependencies"
    )
    parser_export.add_argument("module", help="Module name")
    parser_export.add_argument(
        "--format",
        "-f",
        choices=["dot", "json", "mermaid"],
        default="dot",
        help="Export format (default: dot)",
    )
    parser_export.add_argument(
        "--depth",
        "-d",
        type=int,
        default=0,
        help="Depth to expand (0=unlimited, default: 0)",
    )
    parser_export.add_argument("-o", "--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    db_path = args.db_path
    if not db_path:
        db_path = find_vtags_db()

    if not db_path:
        print(
            "Error: vtags.db not found. Use -db option to specify path.",
            file=sys.stderr,
        )
        return 1

    try:
        vtags_install_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if vtags_install_path not in sys.path:
            sys.path.insert(0, vtags_install_path)

        from Standalone import TraceAPI

        api = TraceAPI(db_path)
    except Exception as e:
        print(f"Error: Failed to initialize vtags: {e}", file=sys.stderr)
        return 1

    try:
        if args.command == "trace":
            result = api.get_module_trace(args.module)
            print_module_trace(result, args.json)

        elif args.command == "topo":
            result = api.get_module_topo(args.module, args.depth)
            print_module_topo(result, args.json)

        elif args.command == "files":
            result = api.get_module_filelist(args.module)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for f in result:
                    print(f)

        elif args.command == "tops":
            result = api.get_all_top_modules()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for i, m in enumerate(result):
                    print(f"{i}: {m}")

        elif args.command == "info":
            result = api.get_module_info(args.module)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if not result:
                    print(f"Module '{args.module}' not found.")
                    return 1
                print(f"Module: {result['name']}")
                print(f"File: {result['file']}")
                print(f"Line: {result['line'] + 1}")
                print(f"\nIOs ({len(result['ios'])}):")
                for io in result["ios"]:
                    print(f"  {io['type']:7} {io['name']}")
                print(f"\nInstances ({len(result['instances'])}):")
                for inst in result["instances"]:
                    print(f"  {inst['instance']:20} {inst['module']}")

        elif args.command == "search":
            result = api.search_module(args.pattern)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for m in result:
                    print(m)

        elif args.command == "strace":
            show_cond = getattr(args, "show_conditions", False)
            if args.full_path is not None:
                result = api.get_signal_full_paths(
                    args.signal,
                    args.file,
                    args.line - 1,
                    args.column,
                    trace_type="source",
                    max_paths=args.full_path,
                )
                print_full_paths(result, args.json)
            elif args.recursive == 1:
                result = api.trace_signal_source(
                    args.signal, args.file, args.line - 1, args.column, show_cond
                )
                print_signal_trace(result, args.json)
            else:
                max_depth = args.recursive if args.recursive > 0 else 999
                result = api.trace_signal_source_recursive(
                    args.signal, args.file, args.line - 1, args.column, max_depth
                )
                print_recursive_trace(result, args.json)

        elif args.command == "dtrace":
            show_cond = getattr(args, "show_conditions", False)
            if args.full_path is not None:
                result = api.get_signal_full_paths(
                    args.signal,
                    args.file,
                    args.line - 1,
                    args.column,
                    trace_type="dest",
                    max_paths=args.full_path,
                )
                print_full_paths(result, args.json)
            elif args.recursive == 1:
                result = api.trace_signal_dest(
                    args.signal, args.file, args.line - 1, args.column, show_cond
                )
                print_signal_trace(result, args.json)
            else:
                max_depth = args.recursive if args.recursive > 0 else 999
                result = api.trace_signal_dest_recursive(
                    args.signal, args.file, args.line - 1, args.column, max_depth
                )
                print_recursive_trace(result, args.json)

        elif args.command == "vcd":
            if not os.path.isfile(args.vcd_file):
                print(f"Error: VCD file not found: {args.vcd_file}", file=sys.stderr)
                return 1

            if args.list:
                result = api.list_vcd_signals(args.vcd_file, args.pattern)
                print_vcd_list(result, args.json)
            elif args.signal:
                file_path = args.file
                line_num = args.line - 1 if args.line else None
                result = api.analyze_signal_waveform(
                    args.vcd_file, args.signal, file_path, line_num
                )
                print_vcd_analysis(result, args.json, args.max_timeline)
            else:
                result = api.list_vcd_signals(args.vcd_file, args.pattern)
                print_vcd_list(result, args.json)

        elif args.command == "export-deps":
            result = api.export_dependencies(args.module, args.depth, args.format)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(result)
                print(f"Dependencies exported to {args.output}")
            else:
                print(result)

        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
