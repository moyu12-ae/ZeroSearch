"""
Smart Rate Limiter - 智能速率限制器

Phase 7 新增功能

问题:
- 当前使用固定间隔（15-30秒）
- 没有根据结果质量动态调整
- 无法自适应网络状况

解决方案:
- 自适应调整：根据结果质量调整速率
- CAPTCHA 检测：触发冷却
- 结果丰富：降低速率
- 结果稀少：加快速率
- 统计追踪：记录调整历史

调整策略:
- CAPTCHA 检测: 触发冷却 (+30s)
- 结果丰富 (>10 citations): 降低速率 (-5s)
- 结果稀少 (<3 citations): 加快速率 (+3s)
- 正常结果: 保持当前速率

使用方式:
    from scripts.smart_rate_limiter import SmartRateLimiter

    limiter = SmartRateLimiter()

    # 搜索后：根据结果调整
    limiter.adjust_based_on_result(result)

    # 等待（如需要）
    wait_time = limiter.wait_if_needed()
"""

import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class AdjustmentResult:
    """调整结果"""
    adjusted: bool
    reason: str
    old_interval: float
    new_interval: float
    cooldown_triggered: bool = False


@dataclass
class AdjustmentStats:
    """调整统计"""
    total_adjustments: int = 0
    cooldown_triggered: int = 0
    speed_up_count: int = 0
    slow_down_count: int = 0
    captcha_count: int = 0
    avg_interval: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_adjustments': self.total_adjustments,
            'cooldown_triggered': self.cooldown_triggered,
            'speed_up_count': self.speed_up_count,
            'slow_down_count': self.slow_down_count,
            'captcha_count': self.captcha_count,
            'avg_interval': self.avg_interval,
        }


class SmartRateLimiterConfig:
    """智能速率限制器配置"""

    def __init__(
        self,
        min_interval: float = 15.0,
        max_interval: float = 30.0,
        adjustment_threshold_high: int = 10,
        adjustment_threshold_low: int = 3,
        speed_up_delta: float = 3.0,
        slow_down_delta: float = 5.0,
        cooldown_delta: float = 30.0,
    ):
        """
        初始化配置

        Args:
            min_interval: 最小间隔（秒）
            max_interval: 最大间隔（秒）
            adjustment_threshold_high: 结果丰富阈值（引用数 > 此值时降低速率）
            adjustment_threshold_low: 结果稀少阈值（引用数 < 此值时加快速率）
            speed_up_delta: 加快速率增量（秒）
            slow_down_delta: 降低速率增量（秒）
            cooldown_delta: CAPTCHA 冷却增量（秒）
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.adjustment_threshold_high = adjustment_threshold_high
        self.adjustment_threshold_low = adjustment_threshold_low
        self.speed_up_delta = speed_up_delta
        self.slow_down_delta = slow_down_delta
        self.cooldown_delta = cooldown_delta


class SmartRateLimiter:
    """
    智能速率限制器

    功能:
    - 自适应调整：根据结果质量动态调整速率
    - CAPTCHA 冷却：检测到 CAPTCHA 时增加间隔
    - 统计追踪：记录调整历史和统计
    - 状态持久化：保存调整状态

    使用方式:
        limiter = SmartRateLimiter()

        # 等待（如需要）
        wait_time = limiter.wait_if_needed()

        # 执行搜索...

        # 调整速率
        result = limiter.adjust_based_on_result(search_result)
        if result.adjusted:
            print(f"调整: {result.reason}")
    """

    DEFAULT_CONFIG = SmartRateLimiterConfig()

    def __init__(
        self,
        config: Optional[SmartRateLimiterConfig] = None,
        state_file: Optional[Path] = None,
    ):
        """
        初始化智能速率限制器

        Args:
            config: 速率限制配置
            state_file: 状态文件路径
        """
        self.config = config or self.DEFAULT_CONFIG
        self.state_file = state_file

        self._current_interval = (self.config.min_interval + self.config.max_interval) / 2
        self._last_search_time: Optional[float] = None
        self._stats = AdjustmentStats()
        self._adjustment_history: list = []

        self._load_state()

    def _load_state(self):
        """加载持久化状态"""
        if self.state_file and self.state_file.exists():
            try:
                import json
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self._current_interval = data.get('current_interval', self._current_interval)
                    self._stats = AdjustmentStats(**data.get('stats', {}))
                logger.debug(f"Loaded rate limiter state from {self.state_file}")
            except Exception as e:
                logger.warning(f"Failed to load rate limiter state: {e}")

    def _save_state(self):
        """保存状态到文件"""
        if self.state_file:
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                import json
                with open(self.state_file, 'w') as f:
                    json.dump({
                        'current_interval': self._current_interval,
                        'stats': self._stats.to_dict(),
                        'updated_at': datetime.now().isoformat(),
                    }, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save rate limiter state: {e}")

    def wait_if_needed(self) -> float:
        """
        如果需要，等待以维持最小间隔

        Returns:
            等待时间（秒）
        """
        if self._last_search_time is None:
            self._last_search_time = time.time()
            return 0.0

        elapsed = time.time() - self._last_search_time
        if elapsed < self._current_interval:
            wait_time = self._current_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
            return wait_time

        return 0.0

    def record_search(self):
        """记录搜索完成"""
        self._last_search_time = time.time()

    def adjust_based_on_result(self, result: Any) -> AdjustmentResult:
        """
        根据搜索结果调整速率

        Args:
            result: 搜索结果对象或字典

        Returns:
            调整结果
        """
        is_captcha = getattr(result, 'captcha_detected', False)
        if isinstance(result, dict):
            is_captcha = result.get('captcha_detected', False)

        citations_count = 0
        if hasattr(result, 'citations'):
            citations_count = len(result.citations)
        elif isinstance(result, dict):
            citations_count = len(result.get('citations', []))

        old_interval = self._current_interval

        if is_captcha:
            self._current_interval = min(
                self._current_interval + self.config.cooldown_delta,
                self.config.max_interval * 2
            )
            self._stats.captcha_count += 1
            self._stats.cooldown_triggered += 1

            adjustment = AdjustmentResult(
                adjusted=True,
                reason=f"CAPTCHA detected: {self._current_interval:.1f}s",
                old_interval=old_interval,
                new_interval=self._current_interval,
                cooldown_triggered=True,
            )

            logger.warning(f"Rate limit adjusted: CAPTCHA detected, new interval: {self._current_interval:.1f}s")

        elif citations_count > self.config.adjustment_threshold_high:
            self._current_interval = min(
                self._current_interval + self.config.slow_down_delta,
                self.config.max_interval
            )
            self._stats.slow_down_count += 1

            adjustment = AdjustmentResult(
                adjusted=True,
                reason=f"Rich results ({citations_count} citations): slowing down",
                old_interval=old_interval,
                new_interval=self._current_interval,
            )

            logger.info(f"Rate limit adjusted: slow down to {self._current_interval:.1f}s")

        elif citations_count < self.config.adjustment_threshold_low and citations_count > 0:
            self._current_interval = max(
                self._current_interval - self.config.speed_up_delta,
                self.config.min_interval
            )
            self._stats.speed_up_count += 1

            adjustment = AdjustmentResult(
                adjusted=True,
                reason=f"Sparse results ({citations_count} citations): speeding up",
                old_interval=old_interval,
                new_interval=self._current_interval,
            )

            logger.info(f"Rate limit adjusted: speed up to {self._current_interval:.1f}s")

        else:
            adjustment = AdjustmentResult(
                adjusted=False,
                reason="Normal results: no adjustment",
                old_interval=old_interval,
                new_interval=self._current_interval,
            )

        if adjustment.adjusted:
            self._stats.total_adjustments += 1
            self._adjustment_history.append({
                'timestamp': datetime.now().isoformat(),
                'reason': adjustment.reason,
                'old_interval': old_interval,
                'new_interval': self._current_interval,
                'captcha': is_captcha,
                'citations': citations_count,
            })

            if len(self._adjustment_history) > 100:
                self._adjustment_history = self._adjustment_history[-100:]

            self._save_state()

        return adjustment

    def get_current_interval(self) -> float:
        """获取当前间隔"""
        return self._current_interval

    def get_stats(self) -> AdjustmentStats:
        """获取统计信息"""
        return self._stats

    def get_adjustment_history(self) -> list:
        """获取调整历史"""
        return self._adjustment_history.copy()

    def reset(self):
        """重置速率限制器"""
        self._current_interval = (self.config.min_interval + self.config.max_interval) / 2
        self._last_search_time = None
        self._stats = AdjustmentStats()
        self._adjustment_history = []
        self._save_state()
        logger.info("Rate limiter reset")

    def get_status(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            'current_interval': self._current_interval,
            'min_interval': self.config.min_interval,
            'max_interval': self.config.max_interval,
            'stats': self._stats.to_dict(),
            'last_adjustment': self._adjustment_history[-1] if self._adjustment_history else None,
        }


def demo():
    """演示 SmartRateLimiter 的使用"""
    print("=" * 70)
    print("SmartRateLimiter 演示 - Phase 7")
    print("=" * 70)

    limiter = SmartRateLimiter()

    print("\n默认配置:")
    print(f"  最小间隔: {limiter.config.min_interval}s")
    print(f"  最大间隔: {limiter.config.max_interval}s")
    print(f"  丰富阈值: >{limiter.config.adjustment_threshold_high} citations")
    print(f"  稀少阈值: <{limiter.config.adjustment_threshold_low} citations")

    print("\n模拟调整:")

    test_results = [
        {'captcha_detected': False, 'citations': [1, 2, 3]},  # 稀少
        {'captcha_detected': False, 'citations': [1, 2, 3, 4]},  # 稀少
        {'captcha_detected': False, 'citations': [1, 2, 3, 4, 5, 6]},  # 正常
        {'captcha_detected': False, 'citations': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]},  # 丰富
        {'captcha_detected': True, 'citations': []},  # CAPTCHA
    ]

    for i, result in enumerate(test_results, 1):
        adjustment = limiter.adjust_based_on_result(result)
        status = "⚡" if adjustment.adjusted else "➖"
        print(f"\n  {i}. {status} {adjustment.reason}")
        print(f"     当前间隔: {limiter.get_current_interval():.1f}s")

    print("\n统计信息:")
    stats = limiter.get_stats()
    print(f"  总调整次数: {stats.total_adjustments}")
    print(f"  冷却触发: {stats.cooldown_triggered}")
    print(f"  加快次数: {stats.speed_up_count}")
    print(f"  减慢次数: {stats.slow_down_count}")
    print(f"  CAPTCHA 次数: {stats.captcha_count}")

    print("\n" + "=" * 70)
    print("🎉 SmartRateLimiter 演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
