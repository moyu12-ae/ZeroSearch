#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SKILL_DIR/.venv"

echo "🔧 Google AI Mode Skill — 首次安装"

# Step 1: Init submodules
if [ ! -f "$SKILL_DIR/libs/camoufox/README.md" ]; then
    echo "📦 初始化 Camoufox Submodule..."
    cd "$SKILL_DIR"
    git submodule update --init --recursive
fi

# Step 2: Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# Step 3: Activate and install
echo "📥 安装依赖..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SKILL_DIR/libs/camoufox/pythonlib" -q
pip install -r "$SKILL_DIR/requirements.txt" -q

# Step 4: Install Playwright browsers (Camoufox needs Firefox)
echo "🌐 安装 Camoufox 浏览器..."
python3 -m camoufox install

echo ""
echo "✅ 安装完成！在 Claude Code 中说: 'Search Google AI Mode for: ...'"
