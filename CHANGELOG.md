# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.14.2] - 2025-03-26

### Fixed
- Case condition tracing: fix `begin_count` double-counting bug in `_parse_case_branches()`
- Case branches with `begin/end` blocks now correctly identified as `[case: ...]` instead of `[condition: ...]`

## [3.14.1] - 2025-03-26

### Fixed
- VCD signal matching now supports full path format (e.g., `tb_vp_004.signal_name`)
- CLI `--signal` parameter now consistent with Python API behavior
- `--list` output paths can now be used directly with `--signal`

## [3.14.0] - 2025-03-26

### Added
- `case` statement condition tracing support
- Support both shorthand (`case_val: statement;`) and block (`case_val: begin...end`) formats
- Support `case/casez/casex` statements

## [3.13.0] - 2025-03-26

### Added
- Recursive tracing support for `maybe` branches
- Complex expression support (bit-select, concatenation, ternary operator)

### Fixed
- Recursive trace now properly handles all branch types

## [3.12.0] - 2025-03-26

### Added
- VCD waveform analysis (`vcd` command)
- Cross-module tracing (Fallback mechanism)
- Conditional assignment tracing (`--show-conditions`)
- Full instance path display (`--full-path`)
- Top-level port auto-detection
- Signal anomaly detection (stuck-at, X/Z states)

### Improved
- Better signal matching in VCD files
- Instance path determination from code location

## [1.0.0] - 2025-03-26

### Added
- Standalone CLI tool for Verilog code analysis
- OpenCode skill integration
- Module topology visualization
- Signal tracing (source and destination)
- Recursive signal tracing with loop detection
- JSON output format for programmatic access

### Commands
- `tops` - List all top-level modules
- `topo` - Show module hierarchy
- `info` - Display module details (IO, instances)
- `files` - List module and submodules files
- `search` - Search modules with wildcard support
- `strace` - Trace signal source
- `dtrace` - Trace signal destination

### Documentation
- Comprehensive README with usage examples
- Python API documentation
- OpenCode skill definition (SKILL.md)

## [0.9.0] - 2023-02-14

### Added
- Initial standalone version based on vtags Vim plugin
- Basic module analysis and signal tracing

[Unreleased]: https://github.com/Deutschkiller/openTrace-skill/compare/v3.14.0...HEAD
[3.14.0]: https://github.com/Deutschkiller/openTrace-skill/compare/v3.13.0...v3.14.0
[3.13.0]: https://github.com/Deutschkiller/openTrace-skill/compare/v3.12.0...v3.13.0
[3.12.0]: https://github.com/Deutschkiller/openTrace-skill/compare/v1.0.0...v3.12.0
[1.0.0]: https://github.com/Deutschkiller/openTrace-skill/releases/tag/v1.0.0
[0.9.0]: https://github.com/Deutschkiller/openTrace-skill/releases/tag/v0.9.0
