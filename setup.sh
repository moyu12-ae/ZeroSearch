#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SKILL_DIR/.venv"
CACHE_DIR="$HOME/.cache/zerosearch"

echo "🔧 ZeroSearch v0.2 — 首次安装"

# Step 1: Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# Step 2: Activate and install dependencies
echo "📥 安装依赖..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r "$SKILL_DIR/requirements.txt" -q

# Step 3: Install Chrome for Testing (Patchright)
echo "🌐 安装 Chrome 浏览器..."
"$VENV_DIR/bin/python" -m patchright install chrome

# Step 4: Create cache directory
mkdir -p "$CACHE_DIR"

echo ""
echo "🎉 ZeroSearch v0.2 安装完成！"
echo "   使用方式: /zerosearch <查询内容>"
echo ""
echo "💡 首次使用时，ZeroSearch 会询问是否设为默认搜索工具。"
