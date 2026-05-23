"""
Profile 持久化管理器

对齐 Architecture v2 §2.1 BrowserEngine。
统一使用独立 Chrome Profile，与用户日常 Chrome 隔离。
Chrome 禁止在默认 Profile 目录上开启 DevTools 远程调试，
因此无法复用真实 Chrome Profile。

Profile 路径: ~/.cache/zerosearch/chrome_profile/
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


# 统一的独立 Profile 路径
DEFAULT_PROFILE_DIR = Path.home() / ".cache" / "zerosearch" / "chrome_profile"


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
        """确保 Profile 目录存在并可用。"""
        if not self._profile_dir.exists():
            self._profile_dir.mkdir(parents=True, exist_ok=True)
            self._is_new = True
        else:
            self._is_new = False

        self._validate_profile()
        return self._profile_dir

    def _validate_profile(self) -> None:
        """验证 Profile 目录完整性。"""
        local_state = self._profile_dir / "Local State"
        default_dir = self._profile_dir / "Default"

        if not local_state.exists() and not default_dir.exists():
            return

        if local_state.exists():
            try:
                with open(local_state, "r") as f:
                    f.read(1024)
            except (IOError, OSError):
                self._recover_corrupted_profile()
                return

        if default_dir.exists():
            try:
                if not default_dir.is_dir():
                    self._recover_corrupted_profile()
            except OSError:
                self._recover_corrupted_profile()

    def _recover_corrupted_profile(self) -> None:
        """备份损坏 Profile 并创建新 Profile。"""
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
                # 备份和移动均失败，仅打印警告，保留原 Profile
                import sys as _sys
                print(
                    f"⚠️  无法备份损坏的 Profile: {backup_path}\n"
                    "    将保留原 Profile 目录，可能影响 Chrome 启动。",
                    file=_sys.stderr,
                )
                return

        self._profile_dir.mkdir(parents=True, exist_ok=True)
        self._is_new = True

        import sys as _sys
        print(
            f"⚠️  Profile 已损坏，已备份至: {backup_path}\n"
            "    已创建全新 Profile。可能需要重新登录 Google。",
            file=_sys.stderr,
        )

    def save_prefs(self, prefs: dict) -> None:
        """保存偏好设置到 Profile。"""
        self.ensure_profile()
        prefs_file = self._profile_dir / "prefs.json"
        with open(prefs_file, "w") as f:
            json.dump(prefs, f, indent=2)

    def load_prefs(self) -> dict:
        """加载偏好设置。"""
        prefs_file = self._profile_dir / "prefs.json"
        if not prefs_file.exists():
            return {}
        try:
            with open(prefs_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def delete_profile(self) -> None:
        """删除当前 Profile。"""
        if self._profile_dir.exists():
            shutil.rmtree(str(self._profile_dir), ignore_errors=True)
        self._is_new = True
