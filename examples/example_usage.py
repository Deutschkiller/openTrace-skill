#!/usr/bin/env python3
"""
openTrace-skill Example Usage

This script demonstrates how to use the TraceAPI for Verilog code analysis.
"""

import sys
import os

sys.path.insert(0, os.path.expanduser("~/vtags"))

from Standalone import TraceAPI


def main():
    vtags_db_path = "./vtags.db"

    if not os.path.isdir(vtags_db_path):
        print(f"Error: {vtags_db_path} not found")
        print("Please generate vtags.db first:")
        print("  find . -name '*.v' > design.f")
        print("  python3 ~/vtags/vtags.py -f design.f")
        return

    api = TraceAPI(vtags_db_path)

    print("=" * 60)
    print("openTrace-skill Example")
    print("=" * 60)

    print("\n1. List top-level modules:")
    tops = api.get_all_top_modules()
    for i, top in enumerate(tops[:5]):
        print(f"   {i}: {top}")

    if not tops:
        print("   No top-level modules found")
        return

    top_module = tops[0]
    print(f"\n2. Module topology of '{top_module}' (depth=2):")
    topo = api.get_module_topo(top_module, depth=2)
    for line in topo.split("\n")[:10]:
        print(f"   {line}")

    print(f"\n3. Module info for '{top_module}':")
    info = api.get_module_info(top_module)
    if info:
        print(f"   File: {info.get('file', 'N/A')}")
        print(f"   Line: {info.get('line', 'N/A')}")
        ios = info.get("ios", [])
        print(f"   IOs: {len(ios)} ports")
        for io in ios[:5]:
            print(f"      {io.get('direction', '?')} {io.get('name', '?')}")

    print(f"\n4. Search modules with pattern '*mng*':")
    modules = api.search_module("*mng*")
    for m in modules[:5]:
        print(f"   - {m}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
