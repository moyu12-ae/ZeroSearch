#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SKILL_DIR/.venv"
CACHE_DIR="$HOME/.cache/zerosearch"

echo "🔧 ZeroSearch v0.4 — 安装"

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
echo "🎉 ZeroSearch v0.4 安装完成！"
echo ""
echo "🧩 Plugin 模式 (推荐):"
echo "   claude --plugin-dir $SKILL_DIR"
echo ""
echo "   然后在 Claude Code 中:"
echo "   /zerosearch:zerosearch-config  (首次配置)"
echo "   /zerosearch:zerosearch <查询>   (搜索)"
echo ""
echo "🧩 Standalone 模式 (备用):"
echo "   触发词: 搜索、search、查一下"
echo "   命令: /zerosearch <查询>"
echo ""
echo "💡 首次搜索时浏览器窗口保持打开 — 登录 Google 一次即可记住。"
