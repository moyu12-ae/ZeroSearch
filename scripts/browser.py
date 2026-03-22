"""
Browser Manager - Connect Mode Only
agent-browser CLI wrapper for Python using Chrome DevTools Protocol (CDP)

This module supports:
- Connect Mode: Connecting to real Chrome via CDP
- Stealth Mode: Launch Chrome with anti-detection parameters

Key anti-detection features:
- --disable-blink-features=AutomationControlled
- --no-sandbox, --no-first-run
- --lang=en-US
"""

import subprocess
import json
import time
import os
import sys
import signal
from pathlib import Path
from typing import Optional, Any, List, Callable, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_DIR = Path.home() / ".cache" / "zero-search" / "chrome_profile"
DEFAULT_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9"
}

STEALTH_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--lang=en-US",
    "--disable-translate",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-background-networking",
    "--disable-sync",
    "--mute-audio",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
]


class BrowserError(Exception):
    """Base exception for browser-related errors"""
    pass


class BrowserNotRunningError(BrowserError):
    """Raised when trying to interact with browser that is not running"""
    pass


class CommandExecutionError(BrowserError):
    """Raised when agent-browser command fails"""
    def __init__(self, command: str, returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Command '{command}' failed with exit code {returncode}: {stderr}")


@dataclass
class PageSnapshot:
    """Represents a page snapshot with accessibility tree"""
    url: str
    title: str
    html: str
    raw_output: str
    refs: dict = None

    def __post_init__(self):
        if self.refs is None:
            self.refs = {}


class BrowserManager:
    """
    Python wrapper for agent-browser CLI - Connect Mode Only.

    This class ONLY supports connecting to real Chrome via CDP.
    All other browser automation modes have been removed.

    Usage:
        # Connect to Chrome on default port 9222
        browser = BrowserManager(connect_port=9222)
        browser.open("https://www.google.com")
        snapshot = browser.snapshot()
        browser.close()

    Args:
        connect_port: CDP port for Chrome debugging (default: 9222)
        timeout: Command timeout in seconds (default: 30)
        max_retries: Maximum number of retries for failed commands (default: 3)
        profile_dir: Directory for persistent cookies storage (default: ~/.cache/zero-search/chrome_profile)
        headers: HTTP headers to set for requests (default: Accept-Language: en-US,en;q=0.9)
    """

    DEFAULT_PORT = 9222
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3

    def __init__(
        self,
        connect_port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
        profile_dir: Optional[Path] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.connect_port = connect_port
        self.timeout = timeout
        self.max_retries = max_retries
        self.profile_dir = profile_dir or DEFAULT_PROFILE_DIR
        self.headers = headers or DEFAULT_HEADERS
        self._is_running = False
        self._current_url: Optional[str] = None
        self._session_id: Optional[str] = None

        self._ensure_profile_dir()

    def _ensure_profile_dir(self) -> None:
        """Ensure profile directory exists"""
        try:
            self.profile_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Profile directory: {self.profile_dir}")
        except Exception as e:
            logger.warning(f"Could not create profile directory: {e}")

    def _get_cookies_file(self) -> Path:
        """Get path to cookies file"""
        return self.profile_dir / "cookies.json"

    def _get_local_state_file(self) -> Path:
        """Get path to Local State file"""
        return self.profile_dir / "Local State"

    @staticmethod
    def find_chrome() -> str:
        """Find Chrome executable path"""
        import platform
        p = platform.system()

        if p == "Darwin":
            paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        elif p == "Windows":
            paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
        else:
            paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
            ]

        for path in paths:
            if Path(path).exists():
                return path

        raise FileNotFoundError("Chrome not found. Please install Google Chrome or Chromium.")

    def launch_stealth_chrome(self, headless: bool = False) -> bool:
        """
        Launch Chrome with anti-detection parameters.

        This launches Chrome with parameters that help avoid CAPTCHA:
        - --disable-blink-features=AutomationControlled
        - --no-sandbox, --no-first-run
        - --lang=en-US

        Args:
            headless: Run in headless mode

        Returns:
            True if Chrome launched successfully
        """
        try:
            chrome_path = self.find_chrome()
        except FileNotFoundError as e:
            logger.error(f"Failed to find Chrome: {e}")
            return False

        args = [
            chrome_path,
            f"--remote-debugging-port={self.connect_port}",
            f"--user-data-dir={self.profile_dir}",
        ] + STEALTH_LAUNCH_ARGS

        if headless:
            args.append("--headless=new")

        logger.info(f"Launching stealth Chrome on port {self.connect_port}...")

        try:
            self._chrome_process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.info(f"Stealth Chrome launched (PID: {self._chrome_process.pid})")

            time.sleep(2)
            self._is_running = True
            return True

        except Exception as e:
            logger.error(f"Failed to launch Chrome: {e}")
            return False

    def stop_stealth_chrome(self) -> bool:
        """
        Stop the stealth Chrome process if we started it.

        Returns:
            True if stopped successfully
        """
        if hasattr(self, "_chrome_process") and self._chrome_process:
            try:
                self._chrome_process.terminate()
                self._chrome_process.wait(timeout=5)
                logger.info("Stealth Chrome stopped")
                return True
            except Exception as e:
                logger.warning(f"Failed to stop Chrome gracefully: {e}")
                try:
                    self._chrome_process.kill()
                    return True
                except:
                    pass
        return False

    def save_cookies(self) -> bool:
        """
        Save cookies from current session to profile directory.

        Returns:
            True if cookies were saved successfully
        """
        if not self._is_running:
            logger.warning("Browser not running, cannot save cookies")
            return False

        try:
            commands = [
                ["connect", str(self.connect_port)],
                ["cookies"]
            ]
            results = self._run_batch_command(commands)

            if len(results) >= 2 and results[1]:
                cookies = results[1]
                if isinstance(cookies, dict) and "cookies" in cookies:
                    cookies = cookies["cookies"]

                cookies_file = self._get_cookies_file()
                with open(cookies_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
                logger.info(f"Saved {len(cookies) if isinstance(cookies, list) else 0} cookies to {cookies_file}")
                return True

        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

        return False

    def load_cookies(self) -> bool:
        """
        Load cookies from profile directory and inject into current session.

        Returns:
            True if cookies were loaded successfully
        """
        if not self._is_running:
            logger.warning("Browser not running, cannot load cookies")
            return False

        cookies_file = self._get_cookies_file()
        if not cookies_file.exists():
            logger.debug("No saved cookies found")
            return False

        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            if not cookies or not isinstance(cookies, list):
                logger.debug("No cookies to load")
                return False

            for cookie in cookies:
                try:
                    commands = [
                        ["connect", str(self.connect_port)],
                        ["cookies", "set", cookie.get("name", ""), cookie.get("value", "")]
                    ]
                    self._run_batch_command(commands)
                except Exception as e:
                    logger.debug(f"Could not set cookie {cookie.get('name')}: {e}")

            logger.info(f"Loaded {len(cookies)} cookies from {cookies_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")

        return False

    def set_local_state(self) -> bool:
        """
        Set Chrome Local State to force English locale.

        This helps ensure AI Mode is available in more regions.

        Returns:
            True if Local State was set successfully
        """
        try:
            local_state_file = self._get_local_state_file()
            local_state = {}

            if local_state_file.exists():
                try:
                    with open(local_state_file, 'r', encoding='utf-8') as f:
                        local_state = json.load(f)
                except Exception:
                    pass

            local_state.update({
                "intl": {
                    "app_locale": "en",
                    "accept_languages": "en-US,en"
                }
            })

            self.profile_dir.mkdir(parents=True, exist_ok=True)
            with open(local_state_file, 'w', encoding='utf-8') as f:
                json.dump(local_state, f, indent=2)

            logger.info("Set Local State to English locale")
            return True

        except Exception as e:
            logger.error(f"Failed to set Local State: {e}")
            return False

    def _run_with_retry(
        self,
        func: Callable[[], Any],
        operation_name: str = "operation"
    ) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            operation_name: Name of operation for logging

        Returns:
            Result of the function

        Raises:
            BrowserError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return func()
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries} attempts")

        raise BrowserError(f"{operation_name} failed: {last_error}")

    def _run_batch_command(self, commands: List[List[str]]) -> List[Any]:
        """
        Run batch commands using JSON format via agent-browser CLI.

        This is the core method for all operations in Connect Mode.
        Commands are executed sequentially and results are parsed from JSON output.

        The output format is:
        [
            {"command": [...], "error": null, "result": {...}, "success": true},
            ...
        ]

        Args:
            commands: List of command arrays, e.g., [["connect", "9222"], ["open", "url"]]

        Returns:
            List of results from each command (extracted from 'result' field)
        """
        cmd = ["agent-browser", "batch", "--json"]
        logger.debug(f"Running batch commands: {commands}")

        try:
            result = subprocess.run(
                cmd,
                input=json.dumps(commands),
                capture_output=True,
                text=True,
                timeout=self.timeout * 2
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise CommandExecutionError(
                    "agent-browser batch",
                    result.returncode,
                    error_msg
                )

            output = result.stdout.strip()
            if not output:
                return []

            try:
                batch_results = json.loads(output)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse batch output: {e}")
                logger.debug(f"Raw output: {output}")
                return []

            if not isinstance(batch_results, list):
                logger.error(f"Unexpected batch output format: {type(batch_results)}")
                return []

            parsed_results = []
            for i, cmd_result in enumerate(batch_results):
                if not isinstance(cmd_result, dict):
                    parsed_results.append(None)
                    continue

                if not cmd_result.get("success", False):
                    error = cmd_result.get("error")
                    cmd_name = cmd_result.get("command", ["unknown"])[0] if cmd_result.get("command") else "unknown"
                    logger.warning(f"Command '{cmd_name}' failed: {error}")
                    parsed_results.append(None)
                    continue

                result_data = cmd_result.get("result")
                parsed_results.append(result_data)

            while len(parsed_results) < len(commands):
                parsed_results.append(None)

            return parsed_results

        except subprocess.TimeoutExpired:
            raise BrowserError(f"Batch command timed out after {self.timeout * 2}s")
        except FileNotFoundError:
            raise BrowserError(
                "agent-browser not found. Please install with: npm install -g agent-browser"
            )

    def _execute_command(self, commands: List[List[str]]) -> Any:
        """
        Execute a batch command with retry logic.

        Args:
            commands: List of command arrays

        Returns:
            Result of the command
        """
        def do_execute():
            results = self._run_batch_command(commands)
            if not results:
                return None
            return results[-1] if results else None

        return self._run_with_retry(do_execute, "batch command")

    def open(self, url: str, set_headers: bool = True) -> None:
        """
        Navigate to URL using Connect Mode.

        Args:
            url: URL to navigate to
            set_headers: If True, set HTTP headers (Accept-Language) (default: True)

        Raises:
            BrowserError: If navigation fails
        """
        def do_open():
            commands = [
                ["connect", str(self.connect_port)],
            ]

            if set_headers and self.headers:
                headers_json = json.dumps(self.headers)
                commands.append(["set", "headers", headers_json])

            commands.append(["open", url])
            results = self._run_batch_command(commands)
            self._is_running = True
            self._current_url = url
            return results

        self._run_with_retry(do_open, f"open {url}")
        logger.info(f"Opened: {url}")

    def goto(self, url: str) -> None:
        """Navigate to URL (alias for open)"""
        self.open(url)

    def close(self) -> None:
        """Close the connection"""
        if not self._is_running:
            logger.warning("Browser is not running, nothing to close")
            return

        try:
            commands = [
                ["connect", str(self.connect_port)],
                ["close"]
            ]
            self._run_batch_command(commands)
            self._is_running = False
            self._current_url = None
            logger.info("Browser closed")
        except BrowserError as e:
            logger.error(f"Error closing browser: {e}")
            raise

    def snapshot(self, interactive: bool = True) -> PageSnapshot:
        """
        Get page accessibility snapshot.

        Args:
            interactive: If True, use -i flag for interactive elements only (recommended)

        Returns:
            PageSnapshot with url, title, html, raw_output, and refs

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running. Call open() first.")

        def do_snapshot():
            args = ["-i"] if interactive else []
            commands = [
                ["connect", str(self.connect_port)],
                ["snapshot"] + args
            ]
            results = self._run_batch_command(commands)

            if not results or len(results) < 2:
                return PageSnapshot(
                    url=self.get_url(),
                    title=self.get_title(),
                    html="",
                    raw_output="",
                    refs={}
                )

            result_data = results[1]
            if result_data is None:
                return PageSnapshot(
                    url=self.get_url(),
                    title=self.get_title(),
                    html="",
                    raw_output="",
                    refs={}
                )

            refs = {}
            raw_output = ""

            if isinstance(result_data, dict):
                refs = result_data.get("refs", {})
                raw_output = result_data.get("snapshot", "")
            elif isinstance(result_data, str):
                raw_output = result_data

            return PageSnapshot(
                url=self.get_url(),
                title=self.get_title(),
                html="",
                raw_output=raw_output,
                refs=refs
            )

        return self._run_with_retry(do_snapshot, "snapshot")

    def get_url(self) -> str:
        """
        Get current page URL.

        Returns:
            Current URL string

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        def do_get_url():
            commands = [
                ["connect", str(self.connect_port)],
                ["get", "url"]
            ]
            results = self._run_batch_command(commands)
            if len(results) >= 2 and results[1]:
                result = results[1]
                if isinstance(result, dict):
                    return result.get("url", "")
                return str(result)
            return ""

        return self._run_with_retry(do_get_url, "get_url")

    def get_title(self) -> str:
        """
        Get current page title.

        Returns:
            Page title string

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        def do_get_title():
            commands = [
                ["connect", str(self.connect_port)],
                ["get", "title"]
            ]
            results = self._run_batch_command(commands)
            if len(results) >= 2 and results[1]:
                result = results[1]
                if isinstance(result, dict):
                    return result.get("title", "")
                return str(result)
            return ""

        return self._run_with_retry(do_get_title, "get_title")

    def wait_for_network_idle(self, timeout_ms: int = 30000) -> bool:
        """
        Wait for network to be idle.

        Args:
            timeout_ms: Maximum time to wait in milliseconds (default: 30000)

        Returns:
            True if network became idle, False if timeout

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        def do_wait():
            commands = [
                ["connect", str(self.connect_port)],
                ["wait", "--load", "networkidle"]
            ]
            results = self._run_batch_command(commands)
            return True

        try:
            self._run_with_retry(do_wait, "wait_network_idle")
            return True
        except BrowserError:
            return False

    def wait_for_element(self, selector: str, timeout_ms: int = 30000) -> bool:
        """
        Wait for an element to appear.

        Args:
            selector: CSS selector or element ref
            timeout_ms: Maximum time to wait in milliseconds

        Returns:
            True if element appeared, False if timeout

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        def do_wait():
            commands = [
                ["connect", str(self.connect_port)],
                ["wait", selector]
            ]
            self._run_batch_command(commands)
            return True

        try:
            self._run_with_retry(do_wait, f"wait_for_element {selector}")
            return True
        except BrowserError:
            return False

    def check_ai_mode_complete(self) -> bool:
        """
        Check if AI Mode is complete (one-time check, no waiting).

        Phase 7: Added for SmartTimeout integration.

        Returns:
            True if AI Mode appears complete, False otherwise
        """
        if not self._is_running:
            return False

        try:
            svg_code = 'document.querySelector(\'button svg[viewBox="3 3 18 18"]\') !== null'
            svg_result = self.eval_js_simple(svg_code)
            if svg_result and svg_result.lower() == 'true':
                return True

            aria_selectors = [
                '[aria-label*="feedback" i]',
                '[aria-label*="related" i]',
                '[aria-label*="source" i]',
            ]
            for selector in aria_selectors:
                aria_code = f'document.querySelector(\'{selector}\') !== null'
                aria_result = self.eval_js_simple(aria_code)
                if aria_result and aria_result.lower() == 'true':
                    return True

            ai_text_indicators = [
                'AI-generated', 'AI Overview', 'Generative AI is experimental',
                'KI-generiert', 'KI-Antworten', 'AI-gegenereerd',
                'Las respuestas de la IA', 'Les réponses de l\'IA', 'Risposte IA'
            ]
            page_text = self.get_page_text()
            if page_text:
                for indicator in ai_text_indicators:
                    if indicator in page_text:
                        return True

        except Exception as e:
            logger.debug(f"AI Mode check failed: {e}")

        return False

    def wait_for_ai_mode_complete(self, timeout_ms: int = 40000) -> bool:
        """
        Wait for AI Mode to complete loading using 3-layer detection.

        This is the GOLD STANDARD for AI Mode detection, adapted from the original
        Playwright implementation.

        Layer 1: SVG thumbs-up icon (most reliable, language-independent)
        Layer 2: aria-label button detection
        Layer 3: Text-based polling (multi-language)

        Args:
            timeout_ms: Maximum time to wait in milliseconds (default: 40000 = 40s)

        Returns:
            True if AI Mode completed, False if timeout
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        logger.info("Starting 3-layer AI Mode detection...")

        layer1_timeout = min(15000, timeout_ms)
        layer2_timeout = min(15000, timeout_ms // 2)
        layer3_timeout = timeout_ms - layer1_timeout - layer2_timeout

        start_time = time.time()

        def layer1_svg_detection() -> bool:
            """Layer 1: SVG thumbs-up icon (most reliable)"""
            try:
                js_code = 'document.querySelector(\'button svg[viewBox="3 3 18 18"]\') !== null'
                result = self.eval_js_simple(js_code)
                if result and result.lower() == 'true':
                    logger.info("Layer 1: SVG thumbs-up icon detected!")
                    return True
            except Exception as e:
                logger.debug(f"Layer 1 SVG check failed: {e}")
            return False

        def layer2_aria_label_detection() -> bool:
            """Layer 2: aria-label button with feedback keyword"""
            try:
                selectors = [
                    '[aria-label*="feedback" i]',
                    '[aria-label*="related" i]',
                    '[aria-label*="source" i]',
                ]
                for selector in selectors:
                    js_code = f'document.querySelector(\'{selector}\') !== null'
                    result = self.eval_js_simple(js_code)
                    if result and result.lower() == 'true':
                        logger.info(f"Layer 2: aria-label button detected: {selector}")
                        return True
            except Exception as e:
                logger.debug(f"Layer 2 aria-label check failed: {e}")
            return False

        def layer3_text_detection() -> bool:
            """Layer 3: Text-based polling (multi-language)"""
            text_indicators = [
                'AI-generated', 'AI Overview', 'Generative AI is experimental',
                'KI-generiert', 'KI-Antworten', 'Generative KI',
                'AI-gegenereerd', 'AI-overzicht',
            ]

            for _ in range(int(layer3_timeout / 1000)):
                try:
                    js_code = 'document.body.innerText'
                    body_text = self.eval_js_simple(js_code) or ''

                    for indicator in text_indicators:
                        if indicator in body_text:
                            logger.info(f"Layer 3: Text indicator detected: {indicator}")
                            return True
                except Exception as e:
                    logger.debug(f"Layer 3 text check failed: {e}")

                time.sleep(1)

                elapsed = (time.time() - start_time) * 1000
                if elapsed >= timeout_ms:
                    break

            return False

        if layer1_svg_detection():
            return True

        if layer2_aria_label_detection():
            return True

        if layer3_text_detection():
            return True

        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"AI Mode detection timeout after {elapsed_ms:.0f}ms")
        return False

    def check_ai_mode_available(self) -> tuple[bool, str]:
        """
        Check if AI Mode is available in current region/language.

        Returns:
            Tuple of (is_available, error_message)
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        not_available_indicators = [
            "AI Mode is not available in your country or language",
            "AI Mode isn't available",
            "Der KI-Modus ist in Ihrem Land oder Ihrer Sprache nicht verfügbar",
            "KI-Modus ist nicht verfügbar",
            "El modo de IA no está disponible en tu país o idioma",
            "La modalità IA non è disponibile nel tuo Paese o nella tua lingua",
            "AI-modus is niet beschikbaar in uw land of taal",
        ]

        try:
            js_code = 'document.body.innerText'
            body_text = self.eval_js_simple(js_code) or ''

            for indicator in not_available_indicators:
                if indicator in body_text:
                    logger.error(f"AI Mode not available: {indicator}")
                    return False, indicator

        except Exception as e:
            logger.debug(f"AI Mode availability check failed: {e}")

        return True, ""

    def eval_js_simple(self, js_code: str) -> str:
        """
        Execute JavaScript code WITHOUT retry logic.
        Use this for simple, fast JS evaluations.

        Args:
            js_code: JavaScript code to execute

        Returns:
            Result of JavaScript execution as string
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running. Call open() first.")

        commands = [
            ["connect", str(self.connect_port)],
            ["eval", js_code]
        ]

        try:
            results = self._run_batch_command(commands)
            if len(results) >= 2 and results[1]:
                result = results[1]
                if isinstance(result, dict):
                    return str(result.get("result", ""))
                return str(result).strip()
        except Exception as e:
            logger.debug(f"eval_js_simple failed: {e}")

        return ""

    def wait(self, seconds: float) -> None:
        """
        Wait for specified seconds.

        Args:
            seconds: Number of seconds to wait
        """
        time.sleep(seconds)
        logger.debug(f"Waited {seconds}s")

    def get_html(self, selector: Optional[str] = None) -> str:
        """
        Get HTML content of page or element.

        Args:
            selector: Optional CSS selector to get HTML of specific element

        Returns:
            HTML content as string

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running. Call open() first.")

        def do_get_html():
            commands = [
                ["connect", str(self.connect_port)],
                ["eval", "document.documentElement.outerHTML"]
            ]
            results = self._run_batch_command(commands)
            if len(results) >= 2 and results[1]:
                result = results[1]
                if isinstance(result, dict):
                    html = result.get("result", "")
                else:
                    html = str(result)
                if html.startswith('"') and html.endswith('"'):
                    html = html[1:-1]
                return html.strip()
            return ""

        return self._run_with_retry(do_get_html, "get_html")

    def eval_js(self, js_code: str) -> str:
        """
        Execute JavaScript code in the page context.

        Args:
            js_code: JavaScript code to execute

        Returns:
            Result of JavaScript execution as string

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running. Call open() first.")

        def do_eval():
            commands = [
                ["connect", str(self.connect_port)],
                ["eval", js_code]
            ]
            results = self._run_batch_command(commands)
            if len(results) >= 2 and results[1]:
                result = results[1]
                if isinstance(result, dict):
                    return str(result.get("result", ""))
                return str(result).strip()
            return ""

        return self._run_with_retry(do_eval, "eval_js")

    def click(self, ref: str) -> bool:
        """
        Click an element by ref.

        Args:
            ref: Element ref like @e1

        Returns:
            True if successful

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        def do_click():
            commands = [
                ["connect", str(self.connect_port)],
                ["click", ref]
            ]
            self._run_batch_command(commands)
            return True

        try:
            self._run_with_retry(do_click, f"click {ref}")
            return True
        except BrowserError:
            return False

    def fill(self, ref: str, text: str) -> bool:
        """
        Fill an input element.

        Args:
            ref: Element ref like @e1
            text: Text to fill

        Returns:
            True if successful

        Raises:
            BrowserNotRunningError: If browser is not running
        """
        if not self._is_running:
            raise BrowserNotRunningError("Browser is not running")

        def do_fill():
            commands = [
                ["connect", str(self.connect_port)],
                ["fill", ref, text]
            ]
            self._run_batch_command(commands)
            return True

        try:
            self._run_with_retry(do_fill, f"fill {ref}")
            return True
        except BrowserError:
            return False

    def is_running(self) -> bool:
        """Check if browser is running"""
        return self._is_running

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close browser"""
        if self._is_running:
            self.close()
        return False


def main():
    """Demo usage"""
    browser = BrowserManager(connect_port=9222)

    try:
        browser.open("https://www.google.com")
        print(f"Title: {browser.get_title()}")
        print(f"URL: {browser.get_url()}")

        snapshot = browser.snapshot()
        print(f"Snapshot received, title: {snapshot.title}")
        print(f"Interactive elements: {len(snapshot.refs)}")

    finally:
        browser.close()


if __name__ == "__main__":
    main()
