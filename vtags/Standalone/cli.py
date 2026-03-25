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

    if sure_list:
        print(f"\nSure {trace_type}:")
        for item in sure_list:
            line_num = int(item["line"]) + 1 if item.get("line") is not None else 0
            print(f"  {item['module']}{item['instance']} {item['file']}:{line_num}")
            print(f"    {item['code']}")

    if maybe_list:
        print(f"\nMaybe {trace_type}:")
        for item in maybe_list:
            line_num = int(item["line"]) + 1 if item.get("line") is not None else 0
            print(f"  {item['module']}{item['instance']} {item['file']}:{line_num}")
            print(f"    {item['code']}")

    if not sure_list and not maybe_list:
        print(f"\nNo {trace_type} found.")


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

    parser_dtrace = subparsers.add_parser("dtrace", help="Trace signal destination")
    parser_dtrace.add_argument("signal", help="Signal name")
    parser_dtrace.add_argument("file", help="File path")
    parser_dtrace.add_argument("line", type=int, help="Line number (1-indexed)")
    parser_dtrace.add_argument(
        "column", nargs="?", type=int, default=0, help="Column number (0-indexed)"
    )

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
            result = api.trace_signal_source(
                args.signal, args.file, args.line - 1, args.column
            )
            print_signal_trace(result, args.json)

        elif args.command == "dtrace":
            result = api.trace_signal_dest(
                args.signal, args.file, args.line - 1, args.column
            )
            print_signal_trace(result, args.json)

        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
