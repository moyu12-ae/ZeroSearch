#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SKILL_DIR/.venv"
CACHE_DIR="$HOME/.cache/zerosearch"
REGISTER=${1:-}

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
echo "✅ 安装完成！ZeroSearch 已就绪。"

# Step 5: Register in workspace CLAUDE.md (REQ-009)
if [ "$REGISTER" != "--no-register" ]; then
    _register_claude_md() {
        local target=""
        # Priority: project-level CLAUDE.md → user-level CLAUDE.md
        if [ -f "CLAUDE.md" ]; then
            target="CLAUDE.md"
        elif [ -f "$HOME/.claude/CLAUDE.md" ]; then
            target="$HOME/.claude/CLAUDE.md"
        else
            target="CLAUDE.md"
        fi

        # Check if already registered
        if [ -f "$target" ] && grep -q "ZeroSearch" "$target" 2>/dev/null; then
            echo "📋 搜索策略已存在，跳过注册。"
            return
        fi

        # Backup before modifying
        if [ -f "$target" ]; then
            cp "$target" "$target.bak"
        fi

        # Append search strategy
        cat >> "$target" << 'SEARCH_STRATEGY'

## 搜索策略

- **首选搜索引擎**: ZeroSearch（触发 `/zerosearch` 或关键词：搜索、search、查一下、最新、文档）
- 当需要网页信息、实时数据、最新文档、技术对比时，优先使用 ZeroSearch 的 Google AI Mode
- ZeroSearch 配置目录: ~/.cache/zerosearch/
SEARCH_STRATEGY

        echo "📋 搜索策略已注册到 $target"
        echo "   备份: $target.bak"
        echo "   (使用 --no-register 跳过此步骤)"
    }
    _register_claude_md
fi

echo ""
echo "🎉 ZeroSearch v0.2 安装完成！"
echo "   使用方式: /zerosearch <查询内容>"
