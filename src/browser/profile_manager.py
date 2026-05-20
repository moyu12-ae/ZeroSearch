"""
Profile 持久化管理器

对齐 Architecture v2 §2.1 BrowserEngine。
支持两种 Profile 模式：
  Option A: 复用真实 Chrome Profile (Google 登录继承)
  Option B: 独立空白 Profile

配置文件: ~/.cache/zerosearch/profile_config.json
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


# Option A: 真实 Chrome Profile 路径
CHROME_PROFILE_DIR = (
    Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
)

# Option B: 独立空白 Profile 路径
DEFAULT_PROFILE_DIR = Path.home() / ".cache" / "zerosearch" / "chrome_profile"

# Profile 配置文件路径
PROFILE_CONFIG_PATH = Path.home() / ".cache" / "zerosearch" / "profile_config.json"


def load_profile_config() -> Optional[dict]:
    """读取 profile_config.json，返回 None 表示首次运行"""
    if not PROFILE_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(PROFILE_CONFIG_PATH.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def save_profile_config(config: dict) -> None:
    """保存 profile_config.json"""
    PROFILE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_CONFIG_PATH.write_text(json.dumps(config, indent=2))


def resolve_profile_path(profile_arg: Optional[str] = None) -> Optional[Path]:
    """根据 profile_config.json 或 CLI 参数解析 Profile 路径。

    优先级: CLI --profile > profile_config.json > None
    --fresh-profile → 强制使用 DEFAULT_PROFILE_DIR

    Args:
        profile_arg: --profile <path> CLI 参数，或 "--fresh-profile"

    Returns:
        Profile 目录路径，返回 None 表示需要触发 AskUserQuestion
    """
    if profile_arg == "--fresh-profile":
        return DEFAULT_PROFILE_DIR

    if profile_arg:
        return Path(profile_arg)

    config = load_profile_config()
    if config is None:
        return None  # 首次运行，需要 AskUserQuestion

    profile_type = config.get("profile", "fresh")
    if profile_type == "chrome":
        return CHROME_PROFILE_DIR
    else:
        return DEFAULT_PROFILE_DIR


class ProfileError(Exception):
    """Profile 相关错误"""


class ProfileManager:
    """Chrome 浏览器 Profile 管理器"""

    def __init__(self, profile_dir: Optional[Path] = None):
        self._profile_dir = profile_dir or DEFAULT_PROFILE_DIR
        self._is_new = False

    @property
    def path(self) -> Path:
        return self._profile_dir

    @property
    def is_new(self) -> bool:
        return self._is_new

    def ensure_profile(self) -> Path:
        """确保 Profile 目录存在并可用。

        Returns:
            Profile 目录路径
        """
        if not self._profile_dir.exists():
            self._profile_dir.mkdir(parents=True, exist_ok=True)
            self._is_new = True
        else:
            self._is_new = False

        self._validate_profile()
        return self._profile_dir

    def _validate_profile(self) -> None:
        """验证 Profile 目录完整性 (Chrome Profile 简单存在性检查)"""
        # Chrome Profile 的核心文件是 Local State 或 Default/
        local_state = self._profile_dir / "Local State"
        default_dir = self._profile_dir / "Default"

        # 新创建的空目录 → 正常
        if not local_state.exists() and not default_dir.exists():
            return

        # 检查 Local State 是否可读
        if local_state.exists():
            try:
                with open(local_state, "r") as f:
                    f.read(1024)  # 读前 1KB 验证可读性
            except (IOError, OSError):
                self._recover_corrupted_profile()
                return

        # 检查 Default/ 是否可访问
        if default_dir.exists():
            try:
                if not default_dir.is_dir():
                    self._recover_corrupted_profile()
            except OSError:
                self._recover_corrupted_profile()

    def _recover_corrupted_profile(self) -> None:
        """备份损坏 Profile 并创建新 Profile"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._profile_dir.parent / (
            f"chrome_profile.corrupted_{timestamp}"
        )

        try:
            shutil.move(str(self._profile_dir), str(backup_path))
        except OSError:
            shutil.rmtree(str(backup_path), ignore_errors=True)
            try:
                shutil.move(str(self._profile_dir), str(backup_path))
            except OSError:
                shutil.rmtree(str(self._profile_dir), ignore_errors=True)

        self._profile_dir.mkdir(parents=True, exist_ok=True)
        self._is_new = True

        print(
            f"⚠️  Profile 已损坏，已备份至: {backup_path}\n"
            "    已创建全新 Profile。可能需要重新登录 Google。"
        )

    def save_prefs(self, prefs: dict) -> None:
        """保存偏好设置到 Profile"""
        self.ensure_profile()
        prefs_file = self._profile_dir / "prefs.json"
        with open(prefs_file, "w") as f:
            json.dump(prefs, f, indent=2)

    def load_prefs(self) -> dict:
        """加载偏好设置"""
        prefs_file = self._profile_dir / "prefs.json"
        if not prefs_file.exists():
            return {}
        try:
            with open(prefs_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def delete_profile(self) -> None:
        """删除当前 Profile"""
        if self._profile_dir.exists():
            shutil.rmtree(str(self._profile_dir), ignore_errors=True)
        self._is_new = True
