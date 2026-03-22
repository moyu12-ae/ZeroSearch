"""
Resilient Search - 错误恢复和重试策略

Phase 7 新增功能

问题:
- 遇到错误直接跳过，缺乏重试和替代查询策略
- 网络临时错误无法自动恢复
- 失败查询没有替代方案

解决方案:
- search_with_retry() - 指数退避重试
- search_with_fallback() - 替代查询策略
- 错误分类和处理策略
- 错误日志和统计

错误分类:
- 网络错误: 重试 3 次，指数退避
- CAPTCHA: 冷却后重试
- 超时: 增加超时后重试
- 未知错误: 记录日志，返回失败

使用方式:
    from scripts.resilient_search import ResilientSearchEngine

    resilient_engine = ResilientSearchEngine(search_engine)
    result = resilient_engine.search_with_retry("query")
"""

import time
import logging
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"
    CAPTCHA = "captcha"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    timeout_increase: float = 1.5


@dataclass
class ErrorResult:
    """错误结果"""
    error_type: ErrorType
    message: str
    retry_count: int
    total_wait_time: float
    recoverable: bool
    original_error: Optional[Exception] = None


class ResilientSearchEngine:
    """
    弹性搜索引擎

    功能:
    - 指数退避重试策略
    - 替代查询策略
    - 错误分类和处理
    - 统计和日志

    使用方式:
        engine = ResilientSearchEngine(search_engine)

        # 带重试的搜索
        result = engine.search_with_retry("query")

        # 带替代查询的搜索
        result = engine.search_with_fallback(
            "original query",
            fallback_queries=["fallback 1", "fallback 2"]
        )
    """

    def __init__(
        self,
        search_engine,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        初始化弹性搜索引擎

        Args:
            search_engine: 底层搜索引擎实例
            retry_config: 重试配置
        """
        self._search_engine = search_engine
        self._retry_config = retry_config or RetryConfig()

        self._stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "retried_searches": 0,
            "fallback_searches": 0,
            "error_types": {},
        }

    def _classify_error(self, error: Exception) -> ErrorType:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()

        if "network" in error_str or "connection" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "captcha" in error_str or "CAPTCHA" in error_type_name:
            return ErrorType.CAPTCHA
        elif "timeout" in error_str or "timeout" in error_type_name:
            return ErrorType.TIMEOUT
        elif "rate" in error_str or "limit" in error_str:
            return ErrorType.RATE_LIMIT
        else:
            return ErrorType.UNKNOWN

    def _get_retry_delay(self, retry_count: int) -> float:
        """
        计算重试延迟（指数退避）

        Args:
            retry_count: 当前重试次数

        Returns:
            延迟时间（秒）
        """
        delay = self._retry_config.base_delay * (self._retry_config.exponential_base ** retry_count)
        return min(delay, self._retry_config.max_delay)

    def _record_error(self, error_type: ErrorType):
        """记录错误统计"""
        self._stats["total_searches"] += 1
        self._stats["failed_searches"] += 1

        error_key = error_type.value
        if error_key not in self._stats["error_types"]:
            self._stats["error_types"][error_key] = 0
        self._stats["error_types"][error_key] += 1

    def _record_success(self):
        """记录成功统计"""
        self._stats["total_searches"] += 1
        self._stats["successful_searches"] += 1

    def search_with_retry(
        self,
        query: str,
        timeout: Optional[int] = None,
        on_retry: Optional[Callable[[int, float], None]] = None,
    ):
        """
        带重试的搜索

        Args:
            query: 搜索查询
            timeout: 超时时间（秒）
            on_retry: 重试回调函数 (retry_count, delay) -> None

        Returns:
            搜索结果或 None
        """
        last_error = None
        total_wait_time = 0.0

        for retry_count in range(self._retry_config.max_retries + 1):
            try:
                current_timeout = timeout
                if retry_count > 0 and timeout:
                    current_timeout = int(timeout * (self._retry_config.timeout_increase ** (retry_count - 1)))

                logger.info(f"Search attempt {retry_count + 1}/{self._retry_config.max_retries + 1}")

                result = self._search_engine.search(
                    query,
                    timeout=current_timeout if current_timeout else 40,
                )

                if retry_count > 0:
                    self._stats["retried_searches"] += 1
                    logger.info(f"Search succeeded after {retry_count} retries")

                self._record_success()
                return result

            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)

                logger.warning(f"Search failed (attempt {retry_count + 1}): {error_type.value} - {e}")

                self._record_error(error_type)

                if retry_count < self._retry_config.max_retries:
                    if error_type == ErrorType.CAPTCHA:
                        delay = 60.0
                    else:
                        delay = self._get_retry_delay(retry_count)

                    total_wait_time += delay
                    logger.info(f"Waiting {delay:.1f}s before retry...")

                    if on_retry:
                        on_retry(retry_count + 1, delay)

                    time.sleep(delay)
                else:
                    logger.error(f"Max retries reached, search failed")

        return None

    def search_with_fallback(
        self,
        primary_query: str,
        fallback_queries: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ):
        """
        带替代查询的搜索

        Args:
            primary_query: 主要查询
            fallback_queries: 替代查询列表
            timeout: 超时时间（秒）

        Returns:
            第一个成功的搜索结果或 None
        """
        queries_to_try = [primary_query]
        if fallback_queries:
            queries_to_try.extend(fallback_queries)

        for i, query in enumerate(queries_to_try):
            is_primary = (i == 0)
            query_type = "主要" if is_primary else f"替代 {i}"

            logger.info(f"Trying {query_type} query: '{query}'")

            result = self.search_with_retry(query, timeout=timeout)

            if result:
                if not is_primary:
                    self._stats["fallback_searches"] += 1
                    logger.info(f"Fallback query {i} succeeded")

                return result

            if is_primary:
                logger.warning(f"Primary query failed, trying fallbacks...")

        logger.error(f"All queries failed")
        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        stats = self._stats.copy()

        if stats["total_searches"] > 0:
            stats["success_rate"] = stats["successful_searches"] / stats["total_searches"]
        else:
            stats["success_rate"] = 0.0

        return stats

    def reset_stats(self):
        """重置统计"""
        self._stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "retried_searches": 0,
            "fallback_searches": 0,
            "error_types": {},
        }
        logger.info("Resilient search statistics reset")

    def get_status(self) -> str:
        """
        获取状态摘要

        Returns:
            格式化的状态字符串
        """
        stats = self.get_stats()

        lines = [
            "Resilient Search Status:",
            f"  Total Searches: {stats['total_searches']}",
            f"  Successful: {stats['successful_searches']}",
            f"  Failed: {stats['failed_searches']}",
            f"  Success Rate: {stats['success_rate'] * 100:.1f}%",
            f"  Retried: {stats['retried_searches']}",
            f"  Fallback: {stats['fallback_searches']}",
        ]

        if stats["error_types"]:
            lines.append("  Error Types:")
            for error_type, count in stats["error_types"].items():
                lines.append(f"    {error_type}: {count}")

        return "\n".join(lines)


def create_resilient_engine(search_engine, **kwargs) -> ResilientSearchEngine:
    """
    便捷工厂函数：创建弹性搜索引擎

    Args:
        search_engine: 底层搜索引擎
        **kwargs: 其他配置参数

    Returns:
        ResilientSearchEngine 实例
    """
    return ResilientSearchEngine(search_engine, **kwargs)


def demo():
    """演示 ResilientSearchEngine 的使用"""
    print("=" * 70)
    print("ResilientSearchEngine 演示 - Phase 7")
    print("=" * 70)

    print("\n模拟错误恢复示例:")
    print("-" * 70)

    from smart_timeout import SmartTimeout

    class MockSearchEngine:
        def __init__(self):
            self.attempt_count = 0

        def search(self, query, timeout=40):
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise Exception("Network error: Connection refused")
            return {"query": query, "citations": ["result1", "result2"]}

    mock_engine = MockSearchEngine()
    resilient = ResilientSearchEngine(mock_engine)

    print("\n模拟搜索（前2次失败，第3次成功）:")

    def on_retry(retry_count, delay):
        print(f"  重试 {retry_count}, 等待 {delay:.1f}s...")

    result = resilient.search_with_retry(
        "test query",
        on_retry=on_retry
    )

    if result:
        print(f"\n✅ 搜索成功!")
    else:
        print(f"\n❌ 搜索失败")

    print("\n统计信息:")
    print(resilient.get_status())

    print("\n" + "=" * 70)
    print("🎉 ResilientSearchEngine 演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
