.PHONY: install clean test help

VTAGS_PATH ?= $(HOME)/vtags
SKILL_PATH ?= $(HOME)/.config/opencode/skills/openTrace-skill

help:
	@echo "openTrace-skill Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install      Install vtags and skill"
	@echo "  make clean        Remove cache and generated files"
	@echo "  make test         Run basic tests"
	@echo "  make uninstall    Remove installed files"

install:
	@./install.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "vtags.db" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf vtags/Parser/parser

test:
	@echo "Testing CLI..."
	@python3 vtags/Standalone/cli.py --help
	@echo ""
	@echo "Basic test passed!"

uninstall:
	rm -rf $(VTAGS_PATH)
	rm -rf $(SKILL_PATH)
	@echo "Uninstalled openTrace-skill"
