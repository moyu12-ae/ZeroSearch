"""
Session Manager - Cookie and State Persistence
Manages browser session state similar to Playwright's Persistent Context

Features:
- Cookie persistence across sessions
- Session state serialization
- Automatic session refresh on expiry
- Multi-profile support
"""

import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Session state data"""
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    last_updated: str
    profile_name: str

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create from dictionary"""
        return cls(**data)


class SessionManager:
    """
    Session Manager for browser state persistence

    Manages cookies, local storage, and session state to provide
    a persistent context similar to Playwright's persistent context.

    Features:
    - Cookie persistence across sessions
    - Session state serialization
    - Automatic session refresh on expiry
    - Profile-based session management

    Usage:
        manager = SessionManager(profile_dir="~/.cache/google-ai-skill")
        state = manager.load_session()
        if state:
            manager.apply_session(browser, state)
        # ... do work ...
        manager.save_session(browser)
    """

    def __init__(
        self,
        profile_dir: Optional[Path] = None,
        profile_name: str = "default",
        cookie_max_age_days: int = 30
    ):
        """
        Initialize session manager

        Args:
            profile_dir: Directory for storing session data
            profile_name: Name of the profile
            cookie_max_age_days: Maximum age for cookies in days
        """
        if profile_dir is None:
            profile_dir = Path.home() / ".cache" / "zero-search" / "sessions"

        self.profile_dir = Path(profile_dir)
        self.profile_name = profile_name
        self.cookie_max_age_days = cookie_max_age_days

        self.profile_dir.mkdir(parents=True, exist_ok=True)

        self._state_file = self.profile_dir / f"{profile_name}_session.json"
        self._last_session_check = 0
        self._session_check_interval = 300

    def _get_state_file(self) -> Path:
        """Get path to session state file"""
        return self.profile_dir / f"{self.profile_name}_session.json"

    def load_session(self) -> Optional[SessionState]:
        """
        Load session state from disk

        Returns:
            SessionState if found and valid, None otherwise
        """
        state_file = self._get_state_file()

        if not state_file.exists():
            logger.debug("No session state file found")
            return None

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            state = SessionState.from_dict(data)

            if not self._is_session_valid(state):
                logger.warning("Session state is expired or invalid")
                return None

            logger.info(f"Loaded session state for profile: {self.profile_name}")
            return state

        except Exception as e:
            logger.error(f"Failed to load session state: {e}")
            return None

    def _is_session_valid(self, state: SessionState) -> bool:
        """
        Check if session state is valid

        Args:
            state: Session state to validate

        Returns:
            True if session is valid
        """
        try:
            last_updated = datetime.fromisoformat(state.last_updated)
            age = datetime.now() - last_updated

            if age > timedelta(days=self.cookie_max_age_days):
                logger.debug(f"Session too old: {age.days} days")
                return False

            if not state.cookies or len(state.cookies) == 0:
                logger.debug("No cookies in session")
                return False

            return True

        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            return False

    def save_session(
        self,
        browser,
        local_storage: Optional[Dict[str, str]] = None,
        session_storage: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Save current session state to disk

        Args:
            browser: BrowserManager instance
            local_storage: Local storage data (optional)
            session_storage: Session storage data (optional)

        Returns:
            True if saved successfully
        """
        try:
            cookies = self._get_browser_cookies(browser)

            if not cookies:
                logger.warning("No cookies to save")
                return False

            state = SessionState(
                cookies=cookies,
                local_storage=local_storage or {},
                session_storage=session_storage or {},
                last_updated=datetime.now().isoformat(),
                profile_name=self.profile_name
            )

            state_file = self._get_state_file()
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Saved session state with {len(cookies)} cookies")
            return True

        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            return False

    def _get_browser_cookies(self, browser) -> List[Dict[str, Any]]:
        """
        Get cookies from browser

        Args:
            browser: BrowserManager instance

        Returns:
            List of cookie dictionaries
        """
        try:
            commands = [
                ["connect", str(browser.connect_port)],
                ["cookies"]
            ]
            results = browser._run_batch_command(commands)

            if len(results) >= 2 and results[1]:
                cookies = results[1]
                if isinstance(cookies, dict) and "cookies" in cookies:
                    return cookies["cookies"]
                if isinstance(cookies, list):
                    return cookies

        except Exception as e:
            logger.debug(f"Failed to get browser cookies: {e}")

        return []

    def apply_session(self, browser, state: SessionState) -> bool:
        """
        Apply session state to browser

        Args:
            browser: BrowserManager instance
            state: Session state to apply

        Returns:
            True if applied successfully
        """
        try:
            applied = 0
            failed = 0

            for cookie in state.cookies:
                try:
                    cookie_name = cookie.get("name", "")
                    cookie_value = cookie.get("value", "")

                    if not cookie_name:
                        continue

                    commands = [
                        ["connect", str(browser.connect_port)],
                        ["cookies", "set", cookie_name, cookie_value]
                    ]
                    browser._run_batch_command(commands)
                    applied += 1

                except Exception as e:
                    logger.debug(f"Failed to set cookie {cookie.get('name')}: {e}")
                    failed += 1

            logger.info(f"Applied session: {applied} cookies set, {failed} failed")
            return applied > 0

        except Exception as e:
            logger.error(f"Failed to apply session: {e}")
            return False

    def apply_local_storage(self, browser, storage: Dict[str, str]) -> bool:
        """
        Apply local storage to browser

        Args:
            browser: BrowserManager instance
            storage: Local storage dictionary

        Returns:
            True if applied successfully
        """
        try:
            for key, value in storage.items():
                escaped_value = json.dumps(value).replace('"', '\\"')
                js_code = f'localStorage.setItem("{key}", "{escaped_value}")'
                browser.eval_js_simple(js_code)

            logger.info(f"Applied {len(storage)} local storage items")
            return True

        except Exception as e:
            logger.error(f"Failed to apply local storage: {e}")
            return False

    def refresh_session(self, browser) -> bool:
        """
        Refresh session by re-authenticating

        Args:
            browser: BrowserManager instance

        Returns:
            True if refreshed successfully
        """
        logger.info("Attempting to refresh session...")

        try:
            browser.open("https://www.google.com")
            time.sleep(2)

            if self.save_session(browser):
                logger.info("Session refreshed successfully")
                return True

        except Exception as e:
            logger.error(f"Session refresh failed: {e}")

        return False

    def clear_session(self) -> bool:
        """
        Clear saved session state

        Returns:
            True if cleared successfully
        """
        state_file = self._get_state_file()

        if state_file.exists():
            try:
                state_file.unlink()
                logger.info(f"Cleared session state: {state_file}")
                return True
            except Exception as e:
                logger.error(f"Failed to clear session: {e}")

        return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about saved session

        Returns:
            Dictionary with session information
        """
        state = self.load_session()

        if not state:
            return {
                "exists": False,
                "profile_name": self.profile_name,
            }

        try:
            last_updated = datetime.fromisoformat(state.last_updated)
            age = datetime.now() - last_updated

            return {
                "exists": True,
                "profile_name": state.profile_name,
                "last_updated": state.last_updated,
                "age_days": age.days,
                "cookie_count": len(state.cookies),
                "local_storage_count": len(state.local_storage),
                "session_storage_count": len(state.session_storage),
            }

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {"exists": False, "error": str(e)}

    def should_check_session(self) -> bool:
        """
        Check if we should verify session validity

        Returns:
            True if session check is due
        """
        current_time = time.time()
        if current_time - self._last_session_check > self._session_check_interval:
            self._last_session_check = current_time
            return True
        return False


def create_session_manager(
    profile_dir: Optional[Path] = None,
    profile_name: str = "default"
) -> SessionManager:
    """
    Factory function to create session manager

    Args:
        profile_dir: Directory for session storage
        profile_name: Name of the profile

    Returns:
        SessionManager instance
    """
    return SessionManager(
        profile_dir=profile_dir,
        profile_name=profile_name
    )
