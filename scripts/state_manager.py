#!/usr/bin/env python3
"""
State Manager - Convenience script for managing authentication state

Usage:
    python state_manager.py setup     # Setup: launch Chrome with debugging, open Google, login
    python state_manager.py save       # Save current state
    python state_manager.py test      # Test with saved state
    python state_manager.py status    # Check current state
"""

import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import BrowserManager, SearchEngine
from scripts.browser_utils import ChromeLauncher, AuthStateManager


DEFAULT_STATE_NAME = "zero-search"
DEFAULT_STATE_DIR = Path.home() / ".agent-browser" / "states"


def setup(args):
    """Setup: Launch Chrome with debugging and open Google for login"""
    print("=" * 60)
    print("🔧 State Manager Setup")
    print("=" * 60)

    state_path = DEFAULT_STATE_DIR / f"{args.name}.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if args.method == "cdp":
        print(f"\n📌 Method: CDP Port ({args.port})")
        print("\n🚀 Launching Chrome with debugging...")

        launcher = ChromeLauncher()
        chrome = launcher.launch()

        if not chrome:
            print("❌ Failed to launch Chrome")
            return 1

        print(f"✅ Chrome launched with PID: {chrome.pid}")
        print(f"\n🔗 CDP Port: {args.port}")
        print(f"📁 State will be saved to: {state_path}")

        print("\n⏳ Waiting for Chrome to start...")
        import time
        time.sleep(3)

        print("\n📝 Next steps:")
        print("   1. In the Chrome window, login to Google")
        print("   2. Come back here and run:")
        print(f"      python state_manager.py save --name {args.name}")
        print("\n   Or press Enter to open Google now...")
        input()

        browser = BrowserManager(cdp_port=args.port, headless=False)
        browser.open("https://www.google.com")
        print("✅ Google opened in Chrome")

    elif args.method == "auto":
        print(f"\n📌 Method: Auto-Connect")
        print("\n⚠️ Make sure Chrome is running with --remote-debugging-port")
        print(f"\n📁 State will be saved to: {state_path}")

        print("\n📝 Next steps:")
        print("   1. Ensure Chrome is running with debugging enabled")
        print("   2. Login to Google in Chrome")
        print("   3. Come back here and run:")
        print(f"      python state_manager.py save --name {args.name}")

    return 0


def save(args):
    """Save current authentication state"""
    print("=" * 60)
    print("💾 State Manager - Save")
    print("=" * 60)

    state_name = args.name or DEFAULT_STATE_NAME
    state_path = DEFAULT_STATE_DIR / f"{state_name}.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Saving state to: {state_path}")

    auth_mgr = AuthStateManager()
    result = auth_mgr.save_state(state_name)

    if result:
        print(f"✅ State saved successfully!")
        print(f"\n📝 To use this state in SearchEngine:")
        print(f"   engine = SearchEngine(state_path='{result}')")
        return 0
    else:
        print("❌ Failed to save state")
        print("\n💡 Make sure Chrome is running with debugging enabled")
        print(f"   Then run: python state_manager.py setup --name {state_name}")
        return 1


def test(args):
    """Test search with saved state"""
    print("=" * 60)
    print("🧪 State Manager - Test")
    print("=" * 60)

    state_name = args.name or DEFAULT_STATE_NAME
    state_path = DEFAULT_STATE_DIR / f"{state_name}.json"

    if not state_path.exists():
        print(f"\n❌ State not found: {state_path}")
        print("\n💡 Run setup first:")
        print(f"   python state_manager.py setup --name {state_name}")
        return 1

    print(f"\n📁 Using state: {state_path}")

    if args.query:
        print(f"\n🔍 Searching: {args.query}")

        engine = SearchEngine(
            state_path=str(state_path),
            headless=False,
        )

        try:
            result = engine.search(args.query)
            print(f"\n✅ Search complete!")
            print(f"   Citations: {len(result.citations)}")
            print(f"\n📄 Output:\n")
            print(result.markdown_output)
        except Exception as e:
            print(f"\n❌ Search failed: {e}")
            return 1
    else:
        print("\n📝 Test mode - opening Google")
        browser = BrowserManager(state_path=str(state_path), headless=False)
        browser.open("https://www.google.com")
        print("✅ Google opened")

    return 0


def status(args):
    """Check current state status"""
    print("=" * 60)
    print("📊 State Manager - Status")
    print("=" * 60)

    auth_mgr = AuthStateManager()
    states = auth_mgr.list_states()

    print(f"\n📁 State directory: {DEFAULT_STATE_DIR}")
    print(f"\n💾 Saved states: {len(states)}")

    if states:
        for state in states:
            state_file = DEFAULT_STATE_DIR / f"{state}.json"
            size = state_file.stat().st_size if state_file.exists() else 0
            print(f"   - {state} ({size:,} bytes)")
    else:
        print("   (none)")

    print(f"\n🔗 CDP Port Check:")
    launcher = ChromeLauncher()
    chrome_path = launcher.get_chrome_path()
    print(f"   Chrome found: {'✅' if chrome_path else '❌'} {chrome_path or 'Not found'}")

    is_running = launcher.is_chrome_running()
    print(f"   Debug port open: {'✅' if is_running else '❌'}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="State Manager - Manage authentication state for Google AI Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Setup (CDP method):
    python state_manager.py setup --name google --method cdp --port 9222

  Setup (auto-connect method):
    python state_manager.py setup --name google --method auto

  Save state:
    python state_manager.py save --name google

  Test search:
    python state_manager.py test --name google --query "EVA 终 日本评价"

  Check status:
    python state_manager.py status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    setup_parser = subparsers.add_parser("setup", help="Setup Chrome with debugging")
    setup_parser.add_argument("--name", default=DEFAULT_STATE_NAME, help="State name")
    setup_parser.add_argument("--method", choices=["cdp", "auto"], default="cdp", help="Connection method")
    setup_parser.add_argument("--port", type=int, default=9222, help="CDP port")

    save_parser = subparsers.add_parser("save", help="Save current state")
    save_parser.add_argument("--name", default=DEFAULT_STATE_NAME, help="State name")

    test_parser = subparsers.add_parser("test", help="Test with saved state")
    test_parser.add_argument("--name", default=DEFAULT_STATE_NAME, help="State name")
    test_parser.add_argument("--query", help="Search query (optional)")

    status_parser = subparsers.add_parser("status", help="Check state status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "setup": setup,
        "save": save,
        "test": test,
        "status": status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
