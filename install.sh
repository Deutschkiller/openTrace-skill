#!/bin/bash

set -e

VTAGS_DIR="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== vtags-standalone 安装程序 ===${NC}\n"

DEFAULT_VTAGS_PATH="$HOME/vtags"
echo -e "请输入 vtags 安装路径 [默认: $DEFAULT_VTAGS_PATH]:"
read -r VTAGS_PATH
VTAGS_PATH="${VTAGS_PATH:-$DEFAULT_VTAGS_PATH}"
VTAGS_PATH="${VTAGS_PATH/#\~/$HOME}"

echo -e "\n${BLUE}[1/5]${NC} 复制 vtags 源码到 $VTAGS_PATH ..."
mkdir -p "$VTAGS_PATH"
cp -r "$VTAGS_DIR/vtags/"* "$VTAGS_PATH/"

echo -e "${BLUE}[2/5]${NC} 编译 C Parser ..."
cd "$VTAGS_PATH/Parser"
if command -v gcc &> /dev/null; then
    if gcc Parser.c -o parser 2>/dev/null; then
        echo -e "${GREEN}Parser 编译成功${NC}"
    else
        echo -e "警告: Parser 编译失败，部分功能可能受限"
    fi
else
    echo -e "警告: 未找到 gcc，跳过 Parser 编译"
fi

echo -e "${BLUE}[3/5]${NC} 生成 skill 配置 ..."
SKILL_DIR="$HOME/.config/opencode/skills/vtags-standalone"
mkdir -p "$SKILL_DIR"

sed "s|{{VTAGS_PATH}}|$VTAGS_PATH|g" "$VTAGS_DIR/skill/SKILL.md" > "$SKILL_DIR/SKILL.md"

echo -e "${BLUE}[4/5]${NC} 设置权限 ..."
chmod +x "$VTAGS_PATH/Standalone/cli.py" 2>/dev/null || true
chmod +x "$VTAGS_PATH/vtags.py" 2>/dev/null || true

echo -e "${BLUE}[5/5]${NC} 验证安装 ..."
if [ -f "$VTAGS_PATH/Standalone/cli.py" ]; then
    echo -e "${GREEN}✓ vtags CLI 已安装${NC}"
fi
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    echo -e "${GREEN}✓ OpenCode skill 已安装${NC}"
fi

echo -e "\n${GREEN}=== 安装完成 ===${NC}\n"
echo -e "vtags 路径: $VTAGS_PATH"
echo -e "Skill 路径: $SKILL_DIR/SKILL.md\n"
echo -e "快速开始:"
echo -e "  1. 进入 Verilog 项目目录"
echo -e "  2. 生成数据库: python3 $VTAGS_PATH/vtags.py -f design.f"
echo -e "  3. 在 OpenCode 中使用 vtags 功能\n"
