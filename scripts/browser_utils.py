#!/usr/bin/env python3
"""
Browser Utilities - Tools for connecting to real Chrome browser

This module provides utilities for:
1. Starting Chrome with remote debugging enabled
2. Saving/loading authentication state
3. Connecting to running Chrome instances

Usage:
    from browser_utils import ChromeLauncher, AuthStateManager

    # Option 1: Launch Chrome with debugging
    launcher = ChromeLauncher()
    launcher.launch()

    # Option 2: Use existing Chrome with auto-connect
    browser = BrowserManager()
    browser._run_command("--auto-connect", "open", url)

    # Option 3: Save/restore auth state
    auth_mgr = AuthStateManager()
    auth_mgr.save_state("google-auth.json")
    auth_mgr.load_state("google-auth.json")
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChromeConfig:
    """Configuration for Chrome browser"""
    debug_port: int = 9222
    user_data_dir: Optional[str] = None
    profile_name: str = "Default"
    headless: bool = False


class ChromeLauncher:
    """
    Launcher for Chrome with remote debugging enabled

    Usage:
        launcher = ChromeLauncher(ChromeConfig(
            debug_port=9222,
            profile_name="Default"
        ))
        launcher.launch()
    """

    CHROME_PATHS = {
        "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "linux": "/usr/bin/google-chrome",
        "win32": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    }

    def __init__(self, config: Optional[ChromeConfig] = None):
        self.config = config or ChromeConfig()

    def get_chrome_path(self) -> Optional[str]:
        """Find Chrome executable path"""
        import platform
        system = platform.system().lower()

        if system == "darwin":
            path = self.CHROME_PATHS["darwin"]
            if Path(path).exists():
                return path

        if system == "linux":
            path = self.CHROME_PATHS["linux"]
            if Path(path).exists():
                return path

        for path in [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]:
            if Path(path).exists():
                return path

        return None

    def launch(self, wait: bool = True) -> Optional[subprocess.Popen]:
        """
        Launch Chrome with remote debugging enabled

        Args:
            wait: If True, wait for Chrome to start

        Returns:
            Popen process or None if failed
        """
        chrome_path = self.get_chrome_path()
        if not chrome_path:
            logger.error("Chrome not found. Please install Chrome.")
            return None

        cmd = [
            chrome_path,
            f"--remote-debugging-port={self.config.debug_port}",
            "--no-first-run",
            "--no-default-browser-check",
        ]

        if self.config.user_data_dir:
            cmd.append(f"--user-data-dir={self.config.user_data_dir}")
        else:
            home = Path.home()
            user_data = home / "Library" / "Application Support" / "Google" / "Chrome"
            if user_data.exists():
                cmd.append(f"--user-data-dir={user_data}")

        cmd.append("--profile-directory=" + self.config.profile_name)

        if self.config.headless:
            cmd.append("--headless=new")

        logger.info(f"Launching Chrome: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if wait:
                import time
                time.sleep(2)

            logger.info(f"Chrome launched with PID: {process.pid}")
            return process

        except Exception as e:
            logger.error(f"Failed to launch Chrome: {e}")
            return None

    def is_chrome_running(self, port: Optional[int] = None) -> bool:
        """Check if Chrome is running with debugging enabled"""
        port = port or self.config.debug_port
        try:
            import urllib.request
            response = urllib.request.urlopen(
                f"http://localhost:{port}/json/version",
                timeout=2
            )
            return response.status == 200
        except:
            return False


class AuthStateManager:
    """
    Manager for saving and loading browser authentication state

    Usage:
        auth_mgr = AuthStateManager()

        # Save current state
        auth_mgr.save_state("google-auth.json")

        # Load state later
        auth_mgr.load_state("google-auth.json")
    """

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path.home() / ".agent-browser" / "states"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, name: str) -> Optional[Path]:
        """
        Save browser authentication state

        Args:
            name: Name for the state file

        Returns:
            Path to saved state file or None if failed
        """
        state_file = self.state_dir / f"{name}.json"

        try:
            subprocess.run(
                ["agent-browser", "--auto-connect", "state", "save", str(state_file)],
                check=True,
                capture_output=True,
            )
            logger.info(f"State saved to: {state_file}")
            return state_file
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to save state: {e}")
            return None

    def load_state(self, name: str) -> bool:
        """
        Load browser authentication state

        Args:
            name: Name of the state file

        Returns:
            True if successful
        """
        state_file = self.state_dir / f"{name}.json"
        if not state_file.exists():
            logger.error(f"State file not found: {state_file}")
            return False

        try:
            subprocess.run(
                ["agent-browser", "--auto-connect", "state", "load", str(state_file)],
                check=True,
                capture_output=True,
            )
            logger.info(f"State loaded from: {state_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to load state: {e}")
            return False

    def list_states(self) -> list[str]:
        """List all saved states"""
        return [f.stem for f in self.state_dir.glob("*.json")]


def main():
    """Demo usage"""
    print("=== Browser Utilities Demo ===\n")

    print("1. Chrome Launcher")
    launcher = ChromeLauncher()
    chrome_path = launcher.get_chrome_path()
    print(f"   Chrome path: {chrome_path or 'Not found'}")
    print(f"   Is running with debug: {launcher.is_chrome_running()}")

    print("\n2. Auth State Manager")
    auth_mgr = AuthStateManager()
    states = auth_mgr.list_states()
    print(f"   Saved states: {states if states else 'None'}")

    print("\n=== How to Use ===")
    print("""
# Method 1: Launch Chrome with debugging
from browser_utils import ChromeLauncher
launcher = ChromeLauncher()
launcher.launch()

# Then in another terminal:
agent-browser --cdp 9222 open https://google.com

# Method 2: Save/Load authentication state
from browser_utils import AuthStateManager
auth_mgr = AuthStateManager()
auth_mgr.save_state("google")

# Later:
auth_mgr.load_state("google")
agent-browser --state google.json open https://google.com
""")


if __name__ == "__main__":
    main()
