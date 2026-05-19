"""
venv 包装器 (T5.1.1) — 兼容原 run.py 接口

确保搜索脚本在独立的 Python 虚拟环境中执行:
1. 自动检测或创建 .venv
2. 安装 Camoufox submodule 与 requirements.txt 依赖
3. 将用户参数完整转发到 src/search/cli.py

设计来源与参考:
  - .anws/v1/04_SYSTEM_DESIGN/search-engine.md §4.3 内部模块结构
  - 原项目 setup.sh (同级目录) 的 venv 创建 + 依赖安装逻辑

调用方式:
    python src/search/run.py --query "React hooks 2026"
    python src/search/run.py --query "React hooks" --debug --save
    python src/search/run.py --query "React hooks" --show-browser
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _locate_project_root() -> Path:
    """定位项目根目录 (包含 setup.sh 的目录)。

    Returns:
        项目根目录的绝对路径
    """
    # run.py 位于 src/search/run.py，向上 3 级即项目根
    this_file = Path(__file__).resolve()
    candidates = [
        this_file.parents[2],  # src/search/run.py → 项目根
    ]
    for candidate in candidates:
        if (candidate / "setup.sh").exists():
            return candidate
    # fallback: 假设 CWD 是项目根
    return Path.cwd()


def _ensure_venv(project_root: Path) -> Path:
    """确保 .venv 存在，不存在则创建。

    Args:
        project_root: 项目根目录路径

    Returns:
        .venv 目录的路径
    """
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
    """获取 venv 中的 Python 解释器路径。

    Args:
        venv_dir: .venv 目录路径

    Returns:
        venv 内 python 可执行文件的绝对路径
    """
    if sys.platform == "win32":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"
    return str(candidate.resolve())


def _needs_install(venv_python: str) -> bool:
    """检查 venv 中是否缺少依赖 (检查 camoufox 和 beautifulsoup4)。

    Args:
        venv_python: venv 内 python 可执行文件路径

    Returns:
        True 表示需要安装依赖
    """
    check_script = "import camoufox, bs4, markdownify; print('OK')"
    result = subprocess.run(
        [venv_python, "-c", check_script],
        capture_output=True,
        text=True,
    )
    return result.returncode != 0


def _detect_externally_managed(venv_python: str) -> bool:
    """检测 venv 中的 pip 是否需要 --break-system-packages 标志。

    某些 Homebrew 安装的 Python (如 3.14) 即使创建了 venv，
    pip 仍会触发 externally-managed-environment 错误。

    Args:
        venv_python: venv 内 python 可执行文件路径

    Returns:
        True 表示需要 --break-system-packages
    """
    try:
        result = subprocess.run(
            [venv_python, "-m", "pip", "install", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 检查是否有 --break-system-packages 选项
        return "--break-system-packages" in result.stdout
    except Exception:
        return False


def _pip_install(venv_python: str, args: list[str], cwd: str) -> None:
    """在 venv 中执行 pip install，自动处理 externally-managed-environment。

    Args:
        venv_python: venv 内 python 可执行文件路径
        args: pip install 的参数列表 (不含 pip install 本身)
        cwd: 工作目录
    """
    cmd = [venv_python, "-m", "pip", "install"] + args
    if _detect_externally_managed(venv_python):
        cmd.append("--break-system-packages")
    subprocess.run(cmd, check=True, cwd=cwd)


def _install_deps(project_root: Path, venv_python: str) -> None:
    """在 venv 中安装 Camoufox submodule 与 requirements.txt 依赖。

    Args:
        project_root: 项目根目录
        venv_python: venv 内 python 可执行文件路径
    """
    print("[run.py] 正在安装依赖...")

    # 检查 submodule 是否已初始化
    submodule_readme = project_root / "libs" / "camoufox" / "README.md"
    if not submodule_readme.is_file():
        print("[run.py] 正在初始化 Camoufox Submodule...")
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            check=True,
            cwd=str(project_root),
        )

    # 安装 Camoufox 库
    camoufox_pythonlib = project_root / "libs" / "camoufox" / "pythonlib"
    if camoufox_pythonlib.is_dir():
        _pip_install(
            venv_python,
            ["-e", str(camoufox_pythonlib), "-q"],
            cwd=str(project_root),
        )

    # 安装 requirements.txt
    requirements_file = project_root / "requirements.txt"
    if requirements_file.is_file():
        _pip_install(
            venv_python,
            ["-r", str(requirements_file), "-q"],
            cwd=str(project_root),
        )

    print("[run.py] 依赖安装完成。")


def main() -> int:
    """venv 包装器主入口。

    1. 定位项目根目录
    2. 确保 .venv 存在并安装依赖
    3. 将命令行参数转发给 src/search/cli.py

    Returns:
        cli.py 的退出码
    """
    project_root = _locate_project_root()
    venv_dir = _ensure_venv(project_root)
    venv_python = _get_venv_python(venv_dir)

    if _needs_install(venv_python):
        _install_deps(project_root, venv_python)

    # 将 run.py 自身的参数转发给 cli.py
    cli_path = project_root / "src" / "search" / "cli.py"
    cmd = [venv_python, str(cli_path)] + sys.argv[1:]

    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
