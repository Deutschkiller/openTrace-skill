# openTrace-skill Examples

This directory contains usage examples for openTrace-skill.

## Files

| File | Description |
|------|-------------|
| `example_usage.py` | Python API usage example |
| `simple_design.v` | Simple Verilog design for testing |

## Running Examples

```bash
# Generate vtags.db first
cd /path/to/examples
find . -name "*.v" > design.f
python3 ~/vtags/vtags.py -f design.f

# Run Python example
python3 example_usage.py
```

## CLI Examples

```bash
# List top modules
python3 ~/vtags/Standalone/cli.py tops

# Show module topology
python3 ~/vtags/Standalone/cli.py topo top_module

# Get module info
python3 ~/vtags/Standalone/cli.py info top_module

# Search modules
python3 ~/vtags/Standalone/cli.py search "*_mng*"

# Trace signal source
python3 ~/vtags/Standalone/cli.py strace signal_name file.v 100

# Recursive trace (5 levels)
python3 ~/vtags/Standalone/cli.py strace signal_name file.v 100 -r 5
```
