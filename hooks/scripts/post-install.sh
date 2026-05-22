#!/bin/bash
# ZeroSearch post-install hook — runs after setup.sh completes
# Triggers: PostToolUse hook when setup.sh is executed

echo "[ZeroSearch] 安装后检查..."

# Check Python version
python3 --version || {
    echo "[ZeroSearch] 警告: Python 3 未找到，请安装 Python >=3.10"
    exit 1
}

# Check Chrome installed (for daemon mode)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -d "/Applications/Google Chrome.app" ]; then
        echo "[ZeroSearch] Chrome 已检测到"
    else
        echo "[ZeroSearch] 提示: Chrome 未检测到，Daemon 模式需要 Chrome 浏览器"
    fi
fi

echo "[ZeroSearch] 安装完成！使用 /zerosearch-config 配置搜索偏好。"
