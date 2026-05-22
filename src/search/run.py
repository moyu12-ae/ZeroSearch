"""
venv 包装器 — 兼容原 run.py 接口

确保搜索脚本在独立的 Python 虚拟环境中执行:
1. 自动检测或创建 .venv
2. 安装 Patchright + requirements.txt 依赖
3. 将用户参数完整转发到 src/search/cli.py

调用方式:
    python src/search/run.py --query "React hooks 2026"
    python src/search/run.py --query "React hooks" --debug --save
    python src/search/run.py --query "React hooks" --profile "/path/to/profile"
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _locate_project_root() -> Path:
    """定位项目根目录 (包含 setup.sh 的目录)。"""
    this_file = Path(__file__).resolve()
    candidates = [
        this_file.parents[2],  # src/search/run.py → 项目根
    ]
    for candidate in candidates:
        if (candidate / "setup.sh").exists():
            return candidate
    return Path.cwd()


def _ensure_venv(project_root: Path) -> Path:
    """确保 .venv 存在，不存在则创建。"""
    venv_dir = project_root / ".venv"
    if not venv_dir.is_dir():
        print("[run.py] 未检测到 .venv，正在创建...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            cwd=str(project_root),
        )
        print(f"[run.py] .venv 创建完成: {venv_dir}")
    return venv_dir


def _get_venv_python(venv_dir: Path) -> str:
    """获取 venv 中的 Python 解释器路径。"""
    if sys.platform == "win32":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"
    return str(candidate.resolve())


def _needs_install(venv_python: str) -> bool:
    """检查 venv 中是否缺少依赖。"""
    check_script = "import patchright, bs4, markdownify; print('OK')"
    result = subprocess.run(
        [venv_python, "-c", check_script],
        capture_output=True,
        text=True,
    )
    return result.returncode != 0


def _pip_install(venv_python: str, args: list[str], cwd: str) -> None:
    """在 venv 中执行 pip install。

    先尝试不带 --break-system-packages 的正常安装，
    失败时自动追加该标志重试（兼容 Debian/Ubuntu externally-managed 环境）。
    """
    cmd = [venv_python, "-m", "pip", "install"] + args
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError:
        cmd.append("--break-system-packages")
        subprocess.run(cmd, check=True, cwd=cwd)


def _install_deps(project_root: Path, venv_python: str) -> None:
    """在 venv 中安装 Patchright 与 requirements.txt 依赖。"""
    print("[run.py] 正在安装依赖...")

    requirements_file = project_root / "requirements.txt"
    if requirements_file.is_file():
        _pip_install(
            venv_python,
            ["-r", str(requirements_file), "-q"],
            cwd=str(project_root),
        )

    print("[run.py] 依赖安装完成。")


def main() -> int:
    """venv 包装器主入口。"""
    project_root = _locate_project_root()
    venv_dir = _ensure_venv(project_root)
    venv_python = _get_venv_python(venv_dir)

    if _needs_install(venv_python):
        _install_deps(project_root, venv_python)

    cli_path = project_root / "src" / "search" / "cli.py"
    if not cli_path.is_file():
        print(f"[run.py] 错误: 找不到 {cli_path}", file=sys.stderr)
        return 1

    cmd = [venv_python, str(cli_path)] + sys.argv[1:]

    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
