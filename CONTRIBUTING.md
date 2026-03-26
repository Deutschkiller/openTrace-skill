# Contributing to openTrace-skill

Thank you for your interest in contributing to openTrace-skill!

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Deutschkiller/openTrace-skill/issues)
2. If not, create a new issue using the Bug Report template
3. Include:
   - Python version
   - OS and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs

### Suggesting Features

1. Open an issue using the Feature Request template
2. Describe the feature and its use case
3. Explain why it would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Deutschkiller/openTrace-skill.git
cd openTrace-skill

# Install dependencies (optional, for VCD support)
pip install -r requirements.txt

# Compile Parser
cd vtags/Parser && gcc Parser.c -o parser && cd ../..

# Run CLI
python3 vtags/Standalone/cli.py --help
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to public functions
- Keep functions focused and small

## Testing

Before submitting a PR, test with a real Verilog project:

```bash
# Generate vtags.db
cd /path/to/verilog/project
find . -name "*.v" > design.f
python3 /path/to/openTrace-skill/vtags/vtags.py -f design.f

# Test commands
python3 /path/to/openTrace-skill/vtags/Standalone/cli.py tops
python3 /path/to/openTrace-skill/vtags/Standalone/cli.py topo <module>
python3 /path/to/openTrace-skill/vtags/Standalone/cli.py info <module>
```

## License

By contributing, you agree that your contributions will be licensed under the BSD 2-Clause License.
