"""
Configuration Module - Centralized configuration management
Provides cross-platform path configuration for profiles and caches
"""

import os
import platform
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration container"""
    profile_base_dir: Path
    cache_dir: Path
    data_dir: Path
    temp_dir: Path


class ConfigManager:
    """
    Cross-platform configuration manager

    Manages paths for profiles, caches, and data storage
    following platform-specific conventions.
    """

    APP_NAME = "zero-search"

    @staticmethod
    def get_platform() -> str:
        """Get current platform name"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        return system

    @staticmethod
    def get_config_dir() -> Path:
        """
        Get platform-specific config directory

        - macOS: ~/Library/Application Support/
        - Linux: ~/.config/
        - Windows: %APPDATA%
        """
        system = ConfigManager.get_platform()

        if system == "macos":
            base = Path.home() / "Library" / "Application Support"
        elif system == "windows":
            base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        else:
            base = Path.home() / ".config"

        return base / ConfigManager.APP_NAME

    @staticmethod
    def get_cache_dir() -> Path:
        """
        Get platform-specific cache directory

        - macOS: ~/Library/Caches/
        - Linux: ~/.cache/
        - Windows: %LOCALAPPDATA%\\Cache
        """
        system = ConfigManager.get_platform()

        if system == "macos":
            base = Path.home() / "Library" / "Caches"
        elif system == "windows":
            base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        else:
            base = Path.home() / ".cache"

        return base / ConfigManager.APP_NAME

    @staticmethod
    def get_data_dir() -> Path:
        """
        Get platform-specific data directory

        - macOS: ~/Library/Application Support/
        - Linux: ~/.local/share/
        - Windows: %APPDATA%
        """
        system = ConfigManager.get_platform()

        if system == "macos":
            base = Path.home() / "Library" / "Application Support"
        elif system == "windows":
            base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        else:
            base = Path.home() / ".local" / "share"

        return base / ConfigManager.APP_NAME

    @staticmethod
    def get_temp_dir() -> Path:
        """Get temporary directory"""
        return Path(tempfile.gettempdir()) / ConfigManager.APP_NAME

    @staticmethod
    def get_profile_base_dir() -> Path:
        """Get default profile base directory"""
        return ConfigManager.get_data_dir() / "profiles"

    @classmethod
    def get_config(cls) -> Config:
        """
        Get complete configuration

        Returns:
            Config object with all paths
        """
        return Config(
            profile_base_dir=cls.get_profile_base_dir(),
            cache_dir=cls.get_cache_dir(),
            data_dir=cls.get_data_dir(),
            temp_dir=cls.get_temp_dir(),
        )

    @classmethod
    def ensure_dirs(cls) -> Config:
        """
        Ensure all configuration directories exist

        Returns:
            Config object with all paths (created if needed)
        """
        config = cls.get_config()

        config.profile_base_dir.mkdir(parents=True, exist_ok=True)
        config.cache_dir.mkdir(parents=True, exist_ok=True)
        config.data_dir.mkdir(parents=True, exist_ok=True)

        return config

    @classmethod
    def get_default_profile_path(cls, profile_name: str) -> Path:
        """
        Get default profile path

        Args:
            profile_name: Name of the profile

        Returns:
            Full path to profile directory
        """
        return cls.get_profile_base_dir() / profile_name


def main():
    """Demo usage"""
    config = ConfigManager.ensure_dirs()

    print("=== Configuration ===")
    print(f"Platform: {ConfigManager.get_platform()}")
    print(f"Profile Base: {config.profile_base_dir}")
    print(f"Cache Dir: {config.cache_dir}")
    print(f"Data Dir: {config.data_dir}")
    print(f"Temp Dir: {config.temp_dir}")

    profile_path = ConfigManager.get_default_profile_path("default")
    print(f"\nDefault Profile: {profile_path}")

    print("\nAll directories created successfully!")


if __name__ == "__main__":
    main()
