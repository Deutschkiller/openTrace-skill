# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-03-26

### Added
- Standalone CLI tool for Verilog code analysis
- OpenCode skill integration
- Module topology visualization
- Signal tracing (source and destination)
- Recursive signal tracing with loop detection
- VCD waveform analysis support
- JSON output format for programmatic access

### Features
- `tops` - List all top-level modules
- `topo` - Show module hierarchy
- `info` - Display module details (IO, instances)
- `files` - List module and submodules files
- `search` - Search modules with wildcard support
- `strace` - Trace signal source
- `dtrace` - Trace signal destination
- `vcd` - Analyze VCD waveform files

### Documentation
- Comprehensive README with usage examples
- Python API documentation
- OpenCode skill definition (SKILL.md)

## [0.9.0] - 2023-02-14

### Added
- Initial standalone version based on vtags Vim plugin
- Basic module analysis and signal tracing

[Unreleased]: https://github.com/Deutschkiller/openTrace-skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Deutschkiller/openTrace-skill/releases/tag/v1.0.0
[0.9.0]: https://github.com/Deutschkiller/openTrace-skill/releases/tag/v0.9.0
