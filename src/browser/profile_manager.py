"""
Profile 持久化管理器

对齐 browser-engine.md §7 数据模型。
管理 Camoufox/Firefox 浏览器 Profile 的创建、加载、损坏恢复。
路径: ~/.cache/google-ai-mode-skill/firefox_profile/
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_PROFILE_DIR = Path.home() / ".cache" / "google-ai-mode-skill" / "firefox_profile"
OLD_CHROME_PROFILE_DIR = Path.home() / ".cache" / "google-ai-mode-skill" / "chrome_profile"


class ProfileError(Exception):
    """Profile 相关错误"""


class ProfileManager:
    """浏览器 Profile 管理器"""

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
        # 检测旧 Chrome Profile 并提示迁移
        if OLD_CHROME_PROFILE_DIR.exists() and not self._profile_dir.exists():
            print(
                "⚠️  检测到旧 Chrome Profile 路径: "
                f"{OLD_CHROME_PROFILE_DIR}\n"
                "    Camoufox 使用 Firefox 引擎，Profile 格式不兼容。\n"
                "    将在新位置创建 Firefox Profile。"
            )

        if not self._profile_dir.exists():
            self._profile_dir.mkdir(parents=True, exist_ok=True)
            self._is_new = True
        else:
            self._is_new = False

        self._validate_profile()
        return self._profile_dir

    def _validate_profile(self) -> None:
        """验证 Profile 目录完整性"""
        prefs_file = self._profile_dir / "prefs.json"
        if not prefs_file.exists():
            return  # 新 Profile，正常

        try:
            with open(prefs_file, "r") as f:
                json.load(f)
        except (json.JSONDecodeError, IOError):
            self._recover_corrupted_profile()

    def _recover_corrupted_profile(self) -> None:
        """备份损坏 Profile 并创建新 Profile"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._profile_dir.parent / (
            f"firefox_profile.corrupted_{timestamp}"
        )

        try:
            shutil.move(str(self._profile_dir), str(backup_path))
        except OSError:
            shutil.rmtree(str(backup_path), ignore_errors=True)
            shutil.move(str(self._profile_dir), str(backup_path))

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
