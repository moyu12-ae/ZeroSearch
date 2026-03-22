"""
Smart Timeout - 自适应 AI Mode 超时策略

Phase 7 新增功能
Phase 9 重构: 使用 UnifiedCacheManager

问题:
- AI Mode 生成时间不稳定（12-13秒波动）
- 当前固定 40s 超时，每次都触发警告
- 等待时间过长用户体验差

解决方案:
- 智能超时策略：初始等待 15s，逐步增加
- 自适应算法：根据历史数据动态调整
- 超时统计：追踪超时模式，优化策略
- 最小化警告：只在真正超时时才警告

Phase 9 改进:
- 使用 UnifiedCacheManager 统一缓存管理
- 惰性清理机制
- 固定容量缓存
- 缓冲批量写入
- 项目级缓存目录

算法:
- 初始等待: 15s
- 增量: +5s/次
- 最大: 60s
- 策略: 渐进式等待，减少不必要的长等待
"""

import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path
import json

try:
    from .cache_manager import create_cache, UnifiedCacheManager, CacheConfig
except ImportError:
    from cache_manager import create_cache, UnifiedCacheManager, CacheConfig


logger = logging.getLogger(__name__)


@dataclass
class TimeoutStats:
    """超时统计信息"""
    total_attempts: int = 0
    successful_immediate: int = 0
    successful_with_retry: int = 0
    timeout_total: int = 0
    total_wait_time: float = 0.0
    avg_wait_time: float = 0.0
    avg_actual_time: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "total_attempts": self.total_attempts,
            "successful_immediate": self.successful_immediate,
            "successful_with_retry": self.successful_with_retry,
            "timeout_total": self.timeout_total,
            "total_wait_time": self.total_wait_time,
            "avg_wait_time": self.avg_wait_time,
            "avg_actual_time": self.avg_actual_time,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TimeoutStats":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SmartTimeoutConfig:
    """智能超时配置"""

    def __init__(
        self,
        initial_wait: float = 15.0,
        increment: float = 5.0,
        max_wait: float = 60.0,
        check_interval: float = 1.0,
    ):
        self.initial_wait = initial_wait
        self.increment = increment
        self.max_wait = max_wait
        self.check_interval = check_interval

    @classmethod
    def from_dict(cls, data: Dict) -> "SmartTimeoutConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__init__.__code__.co_varnames[1:]})


class SmartTimeout:
    """
    智能超时管理器

    Phase 9 改进:
    - 使用 UnifiedCacheManager 统一缓存管理
    - 惰性清理机制 (每 N 次调用检查一次)
    - 固定容量缓存
    - 缓冲批量写入
    - 项目级缓存目录

    功能:
    - 渐进式等待策略
    - 自适应超时调整
    - 超时统计追踪
    - 状态持久化
    """

    DEFAULT_CONFIG = SmartTimeoutConfig()

    def __init__(
        self,
        config: Optional[SmartTimeoutConfig] = None,
        state_file: Optional[Path] = None,
        use_cache: bool = True,
    ):
        """
        初始化智能超时管理器

        Args:
            config: 超时配置
            state_file: 状态文件路径（用于持久化统计，已废弃）
            use_cache: 是否使用 UnifiedCacheManager（默认 True）
        """
        self.config = config or self.DEFAULT_CONFIG

        self._stats = TimeoutStats()
        self._last_wait_time = 0.0
        self._last_actual_time = 0.0
        self._is_complete = False
        self._check_counter = 0

        if use_cache and state_file is None:
            self._cache = create_cache(
                name="timeout",
                max_entries=500,
                max_size_mb=5.0,
                buffer_size=20,
                cleanup_ratio=0.5,
                check_interval=10,
            )
            self._use_new_cache = True
            self._load_state_from_cache()
        else:
            self._use_new_cache = False
            self.state_file = state_file
            self._cache = None
            self._load_state()

    def _lazy_cleanup(self):
        """
        惰性清理检查

        每次操作时调用，每 N 次调用才真正检查
        """
        if not self._use_new_cache:
            return

        self._check_counter += 1
        if self._check_counter >= 10:
            self._check_counter = 0
            self._cache.lazy_cleanup_if_needed()

    def _load_state_from_cache(self):
        """从缓存加载状态"""
        if not self._use_new_cache:
            return

        recent = self._cache.get_recent(1)
        if recent:
            data = recent[0]
            if 'stats' in data:
                self._stats = TimeoutStats.from_dict(data['stats'])

    def _load_state(self):
        """加载持久化状态（向后兼容）"""
        if self.state_file and self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    if 'stats' in data:
                        self._stats = TimeoutStats.from_dict(data['stats'])
                    logger.debug(f"Loaded timeout stats from {self.state_file}")
            except Exception as e:
                logger.warning(f"Failed to load timeout state: {e}")

    def _save_state(self):
        """保存状态到文件或缓存"""
        if self._use_new_cache:
            self._cache.append({
                "timestamp": datetime.now().isoformat(),
                "stats": self._stats.to_dict(),
            })
        elif self.state_file:
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump({
                        'stats': self._stats.to_dict(),
                        'last_updated': datetime.now().isoformat(),
                    }, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save timeout state: {e}")

    def wait_for_complete(
        self,
        check_func,
        progress_callback=None,
        on_timeout=None,
    ) -> bool:
        """
        等待完成

        Args:
            check_func: 检查函数，返回 True 表示完成
            progress_callback: 进度回调函数 (attempt, wait_time) -> None
            on_timeout: 超时回调函数 () -> None

        Returns:
            True 表示完成，False 表示超时
        """
        self._lazy_cleanup()

        start_time = time.time()
        self._is_complete = False

        current_wait = self.config.initial_wait
        attempt = 0

        while current_wait <= self.config.max_wait:
            attempt += 1

            logger.debug(f"Timeout attempt {attempt}: waiting {current_wait:.1f}s")

            time.sleep(self.config.check_interval)

            elapsed = time.time() - start_time
            if progress_callback:
                progress_callback(attempt, elapsed)

            if check_func():
                self._is_complete = True
                self._record_success(elapsed)
                return True

            current_wait += self.config.increment

        if on_timeout:
            on_timeout()

        self._record_timeout(time.time() - start_time)
        return False

    def _record_success(self, actual_time: float):
        """记录成功"""
        self._last_wait_time = min(actual_time, self.config.max_wait)
        self._last_actual_time = actual_time

        self._stats.total_attempts += 1
        self._stats.successful_immediate += 1
        self._stats.total_wait_time += self._last_wait_time

        if self._stats.total_attempts > 0:
            self._stats.avg_wait_time = self._stats.total_wait_time / self._stats.total_attempts
            self._stats.avg_actual_time = sum([
                self._stats.avg_actual_time * (self._stats.total_attempts - 1),
                self._last_actual_time
            ]) / self._stats.total_attempts

        self._save_state()

        logger.info(f"AI Mode completed in {actual_time:.1f}s")

    def _record_timeout(self, wait_time: float):
        """记录超时"""
        self._last_wait_time = wait_time
        self._last_actual_time = wait_time

        self._stats.total_attempts += 1
        self._stats.timeout_total += 1
        self._stats.total_wait_time += wait_time

        if self._stats.total_attempts > 0:
            self._stats.avg_wait_time = self._stats.total_wait_time / self._stats.total_attempts

        self._save_state()

        logger.warning(f"AI Mode timeout after {wait_time:.1f}s")

    def get_last_wait_time(self) -> float:
        """获取上次等待时间"""
        return self._last_wait_time

    def get_last_actual_time(self) -> float:
        """获取上次实际完成时间"""
        return self._last_actual_time

    def is_complete(self) -> bool:
        """检查上次调用是否完成"""
        return self._is_complete

    def get_stats(self) -> TimeoutStats:
        """获取统计信息"""
        return self._stats

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self._stats.total_attempts == 0:
            return 0.0
        return (self._stats.total_attempts - self._stats.timeout_total) / self._stats.total_attempts

    def reset_stats(self):
        """重置统计"""
        self._stats = TimeoutStats()
        self._save_state()
        logger.info("Timeout statistics reset")

    def adjust_config_based_on_stats(self):
        """
        根据统计数据调整配置（自适应）

        策略:
        - 如果成功率 > 95% 且平均等待时间 > 20s，减少 initial_wait
        - 如果成功率 < 80%，增加 max_wait
        - 如果超时次数多，增加 increment
        """
        if self._stats.total_attempts < 10:
            return

        success_rate = self.get_success_rate()
        avg_time = self._stats.avg_actual_time

        original_config = {
            'initial_wait': self.config.initial_wait,
            'max_wait': self.config.max_wait,
        }

        if success_rate > 0.95 and avg_time > 20:
            self.config.initial_wait = max(10.0, self.config.initial_wait - 2.0)
            logger.info(f"Adjusted initial_wait: {original_config['initial_wait']} -> {self.config.initial_wait}")

        if success_rate < 0.80:
            self.config.max_wait = min(90.0, self.config.max_wait + 10.0)
            logger.info(f"Adjusted max_wait: {original_config['max_wait']} -> {self.config.max_wait}")

    def get_recommended_timeout(self) -> float:
        """
        获取推荐的默认超时时间

        基于统计数据计算一个合理的默认值
        """
        if self._stats.total_attempts >= 5:
            avg_time = self._stats.avg_actual_time
            p95 = avg_time * 1.5
            return min(p95, self.config.max_wait)
        else:
            return self.config.initial_wait * 2

    def get_status(self) -> Dict:
        """获取状态摘要"""
        result = {
            "config": {
                "initial_wait": self.config.initial_wait,
                "increment": self.config.increment,
                "max_wait": self.config.max_wait,
            },
            "stats": self._stats.to_dict(),
            "success_rate": f"{self.get_success_rate() * 100:.1f}%",
            "recommended_timeout": f"{self.get_recommended_timeout():.1f}s",
        }

        if self._use_new_cache and self._cache:
            result["cache"] = self._cache.get_stats()

        return result

    def get_cache_path(self) -> Optional[str]:
        """获取缓存路径"""
        if self._use_new_cache and self._cache:
            return self._cache.get_cache_path()
        return None


def create_smart_timeout(
    state_file: Optional[Path] = None,
    use_cache: bool = True,
) -> SmartTimeout:
    """
    便捷工厂函数：创建智能超时管理器

    Args:
        state_file: 状态文件路径（已废弃，建议使用 use_cache=True）
        use_cache: 是否使用 UnifiedCacheManager（默认 True）

    Returns:
        SmartTimeout 实例
    """
    return SmartTimeout(state_file=state_file, use_cache=use_cache)


def demo():
    """演示 SmartTimeout 的使用"""
    print("=" * 70)
    print("SmartTimeout 演示 - Phase 9")
    print("=" * 70)

    timeout_mgr = create_smart_timeout(use_cache=True)

    if timeout_mgr.get_cache_path():
        print(f"\n[1] 缓存位置: {timeout_mgr.get_cache_path()}")

    print("\n默认配置:")
    print(f"  初始等待: {timeout_mgr.config.initial_wait}s")
    print(f"  增量: {timeout_mgr.config.increment}s")
    print(f"  最大等待: {timeout_mgr.config.max_wait}s")

    print("\n模拟等待示例:")

    attempt_count = [0]

    def mock_check_func():
        """模拟检查函数 - 随机成功"""
        import random
        attempt_count[0] += 1
        return random.random() > 0.7

    def progress_callback(attempt, elapsed):
        print(f"  尝试 {attempt}: 已等待 {elapsed:.1f}s...")

    success = timeout_mgr.wait_for_complete(
        mock_check_func,
        progress_callback=progress_callback,
    )

    if success:
        print(f"\n✅ 完成! 实际等待时间: {timeout_mgr.get_last_actual_time():.1f}s")
    else:
        print(f"\n❌ 超时! 等待时间: {timeout_mgr.get_last_wait_time():.1f}s")

    print("\n统计信息:")
    stats = timeout_mgr.get_stats()
    print(f"  总尝试: {stats.total_attempts}")
    print(f"  成功: {stats.successful_immediate}")
    print(f"  超时: {stats.timeout_total}")
    print(f"  成功率: {timeout_mgr.get_success_rate() * 100:.1f}%")
    print(f"  平均等待时间: {stats.avg_wait_time:.1f}s")

    print("\n推荐超时时间:")
    print(f"  {timeout_mgr.get_recommended_timeout():.1f}s")


if __name__ == "__main__":
    demo()
