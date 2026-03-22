"""
Rate Limiter - Search Rate Control (Phase 5)
Prevents triggering Google anti-bot mechanisms

Features:
- Configurable delay modes: conservative (30-60s), balanced (15-30s), fast (5-15s)
- Random interval within configured range
- Exponential backoff on detected rate limiting
- Persistent state across sessions
"""

import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitMode(Enum):
    """Rate limiting modes"""
    CONSERVATIVE = "conservative"  # 30-60 seconds
    BALANCED = "balanced"          # 15-30 seconds (Phase 5 default)
    FAST = "fast"                  # 5-15 seconds


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    min_interval: float = 15.0
    max_interval: float = 30.0
    max_backoff: float = 120.0
    initial_backoff: float = 10.0
    backoff_multiplier: float = 2.0
    mode: RateLimitMode = RateLimitMode.BALANCED

    @classmethod
    def from_mode(cls, mode: RateLimitMode) -> "RateLimitConfig":
        """Create config from predefined mode"""
        configs = {
            RateLimitMode.CONSERVATIVE: cls(min_interval=30.0, max_interval=60.0, mode=mode),
            RateLimitMode.BALANCED: cls(min_interval=15.0, max_interval=30.0, mode=mode),
            RateLimitMode.FAST: cls(min_interval=5.0, max_interval=15.0, mode=mode),
        }
        return configs.get(mode, configs[RateLimitMode.BALANCED])


class RateLimiter:
    """
    Rate Limiter for Google Searches (Phase 5)

    Prevents triggering anti-bot mechanisms by enforcing delays
    between consecutive searches.

    Features:
    - Configurable delay modes: conservative, balanced, fast
    - Random interval within configured range
    - Exponential backoff on detected rate limiting
    - Persistent state across sessions

    Usage:
        # Balanced mode (15-30 seconds) - Phase 5 default
        limiter = RateLimiter()

        # Conservative mode (30-60 seconds)
        limiter = RateLimiter(RateLimitConfig.from_mode(RateLimitMode.CONSERVATIVE))

        # Wait before search if needed
        wait_time = limiter.wait_if_needed()
        # ... perform search ...
        limiter.record_search()
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter

        Args:
            config: Rate limit configuration (default: balanced mode 15-30s)
        """
        self.config = config or RateLimitConfig.from_mode(RateLimitMode.BALANCED)
        self._last_search_time: Optional[float] = None
        self._consecutive_rapid: int = 0
        self._current_backoff: float = self.config.initial_backoff
        self._state_file: Optional[Path] = None
        self._random = random.Random()

    def set_state_file(self, path: Path) -> None:
        """
        Set path for persistent state file

        Args:
            path: Path to state file
        """
        self._state_file = path
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file"""
        if not self._state_file or not self._state_file.exists():
            return

        try:
            import json
            with open(self._state_file, 'r') as f:
                state = json.load(f)
                self._last_search_time = state.get('last_search_time')
                self._consecutive_rapid = state.get('consecutive_rapid', 0)
                self._current_backoff = state.get('current_backoff', self.config.initial_backoff)
                logger.debug(f"Loaded rate limit state: last_search={self._last_search_time}")
        except Exception as e:
            logger.warning(f"Failed to load rate limit state: {e}")

    def _save_state(self) -> None:
        """Save state to file"""
        if not self._state_file:
            return

        try:
            import json
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                'last_search_time': self._last_search_time,
                'consecutive_rapid': self._consecutive_rapid,
                'current_backoff': self._current_backoff,
            }
            with open(self._state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"Failed to save rate limit state: {e}")

    def wait_if_needed(self) -> float:
        """
        Wait if needed to maintain minimum interval

        Uses random interval between min_interval and max_interval for each wait.

        Returns:
            Time waited in seconds
        """
        current_time = time.time()

        if self._last_search_time is None:
            self._last_search_time = current_time
            return 0.0

        elapsed = current_time - self._last_search_time

        wait_time = 0.0

        if elapsed < self.config.min_interval:
            remaining = self.config.min_interval - elapsed
            interval_range = self.config.max_interval - self.config.min_interval

            if interval_range > 0:
                random_extra = self._random.uniform(0, interval_range)
                wait_time = remaining + random_extra
            else:
                wait_time = remaining

            logger.info(f"Rate limit: waiting {wait_time:.1f}s before search (mode={self.config.mode.value})")
            time.sleep(wait_time)
            self._consecutive_rapid += 1

            if self._consecutive_rapid > 3:
                self._increase_backoff()
        else:
            if self._consecutive_rapid > 0:
                self._consecutive_rapid = 0
                self._decrease_backoff()

        self._last_search_time = time.time()
        self._save_state()

        return wait_time

    def record_search(self) -> None:
        """Record that a search was performed"""
        self._last_search_time = time.time()
        self._save_state()

    def report_rate_limit(self) -> None:
        """Report that rate limiting was detected - increase backoff"""
        logger.warning("Rate limit detected, increasing backoff")
        self._increase_backoff()

    def _increase_backoff(self) -> None:
        """Increase backoff time"""
        self._current_backoff = min(
            self._current_backoff * self.config.backoff_multiplier,
            self.config.max_backoff
        )
        logger.info(f"Backoff increased to {self._current_backoff:.1f}s")
        self._save_state()

    def _decrease_backoff(self) -> None:
        """Decrease backoff time after successful searches"""
        self._current_backoff = max(
            self._current_backoff / self.config.backoff_multiplier,
            self.config.initial_backoff
        )
        logger.debug(f"Backoff decreased to {self._current_backoff:.1f}s")

    def get_next_wait_time(self) -> float:
        """
        Get the next recommended wait time (without actually waiting)

        Returns:
            Recommended wait time in seconds
        """
        if self._last_search_time is None:
            return 0.0

        elapsed = time.time() - self._last_search_time
        remaining = max(0, self.config.min_interval - elapsed)

        avg_interval = (self.config.min_interval + self.config.max_interval) / 2
        return remaining + avg_interval + self._current_backoff

    def get_status(self) -> dict:
        """
        Get current rate limiter status

        Returns:
            Dictionary with status information
        """
        elapsed = 0.0
        if self._last_search_time:
            elapsed = time.time() - self._last_search_time

        return {
            "mode": self.config.mode.value,
            "min_interval": self.config.min_interval,
            "max_interval": self.config.max_interval,
            "last_search_elapsed": elapsed,
            "consecutive_rapid": self._consecutive_rapid,
            "current_backoff": self._current_backoff,
            "needs_wait": elapsed < self.config.min_interval,
        }

    def reset(self) -> None:
        """Reset rate limiter state"""
        self._last_search_time = None
        self._consecutive_rapid = 0
        self._current_backoff = self.config.initial_backoff
        self._save_state()
        logger.info("Rate limiter reset")


def create_rate_limiter(
    mode: RateLimitMode = RateLimitMode.BALANCED,
    state_file: Optional[Path] = None
) -> RateLimiter:
    """
    Factory function to create rate limiter

    Args:
        mode: Rate limiting mode (default: BALANCED - 15-30s)
        state_file: Path for persistent state

    Returns:
        Configured RateLimiter instance

    Example:
        # Balanced mode (15-30 seconds)
        limiter = create_rate_limiter()

        # Conservative mode (30-60 seconds)
        limiter = create_rate_limiter(mode=RateLimitMode.CONSERVATIVE)
    """
    config = RateLimitConfig.from_mode(mode)
    limiter = RateLimiter(config)

    if state_file:
        limiter.set_state_file(state_file)

    return limiter


def demo():
    """演示 RateLimiter 的使用"""
    print("=" * 60)
    print("RateLimiter 演示 (Phase 5 - 平衡模式)")
    print("=" * 60)

    print("\n1. 平衡模式 (15-30秒):")
    limiter = RateLimiter()

    status = limiter.get_status()
    print(f"   模式: {status['mode']}")
    print(f"   间隔范围: {status['min_interval']}-{status['max_interval']}秒")

    print("\n2. 保守模式 (30-60秒):")
    from_mode = RateLimitConfig.from_mode(RateLimitMode.CONSERVATIVE)
    print(f"   间隔范围: {from_mode.min_interval}-{from_mode.max_interval}秒")

    print("\n3. 快速模式 (5-15秒):")
    from_mode = RateLimitConfig.from_mode(RateLimitMode.FAST)
    print(f"   间隔范围: {from_mode.min_interval}-{from_mode.max_interval}秒")

    print("\n4. 模拟连续搜索 (不实际等待):")
    for i in range(3):
        status = limiter.get_status()
        print(f"   搜索 {i+1}: 需要等待 = {status['needs_wait']}")

    print("\n✅ RateLimiter 演示完成!")


if __name__ == "__main__":
    demo()
