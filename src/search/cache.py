"""LRU + TTL 内存缓存模块。

使用 OrderedDict 实现 LRU 淘汰策略，基于 TTL 自动过期。
查询 key 经过 normalize（lower + strip）后作为缓存键。
"""

import threading
import time
from collections import OrderedDict
from typing import Any


def normalize_key(key: str) -> str:
    """规范化缓存键：小写 + 去除首尾空白。"""
    return key.lower().strip()


class LRUCache:
    """LRU + TTL 内存缓存。

    使用 OrderedDict 维护访问顺序，最近访问的条目移到末尾。
    超过 max_size 时淘汰最久未使用的条目。
    超过 ttl_seconds 的条目自动视为过期。
    """

    def __init__(self, max_size: int = 50, ttl_seconds: int = 300) -> None:
        """初始化缓存。

        Args:
            max_size: 最大缓存条目数，默认 50。
            ttl_seconds: TTL 过期时间（秒），默认 300（5 分钟）。
        """
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _normalize_key(self, key: str) -> str:
        """规范化 key：lower + strip。"""
        return key.lower().strip()

    def _is_expired(self, value: dict[str, Any]) -> bool:
        """检查缓存条目是否已过期。"""
        timestamp = value.get("timestamp", 0.0)
        age = time.monotonic() - timestamp
        return age >= self._ttl_seconds

    def _evict_lru(self) -> None:
        """淘汰最久未使用的条目（OrderedDict 的第一个）。"""
        if self._cache:
            self._cache.popitem(last=False)
            self._evictions += 1

    def _evict_expired(self) -> int:
        """淘汰所有已过期的条目，返回淘汰数量。"""
        expired_keys = []
        for key, value in self._cache.items():
            if self._is_expired(value):
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            self._evictions += 1

        return len(expired_keys)

    def get(self, key: str) -> dict[str, Any] | None:
        """获取缓存值。

        如果条目存在且未过期，将其移到 LRU 队尾（最近使用）并返回。
        如果条目过期，删除并返回 None。
        如果条目不存在，返回 None。

        Args:
            key: 查询 key，会自动规范化（lower + strip）。

        Returns:
            缓存的值字典，或 None。
        """
        normalized = self._normalize_key(key)

        with self._lock:
            if normalized not in self._cache:
                self._misses += 1
                return None

            value = self._cache[normalized]

            if self._is_expired(value):
                del self._cache[normalized]
                self._evictions += 1
                self._misses += 1
                return None

            # 移到队尾（标记为最近使用）
            self._cache.move_to_end(normalized)
            self._hits += 1
            return value

    def put(self, key: str, value: dict[str, Any]) -> None:
        """存入缓存值。

        如果 key 已存在且未过期，更新值并移到队尾。
        如果缓存已满，先淘汰过期条目再淘汰 LRU 条目。
        始终拷贝 value 字典，不修改调用方传入的对象。

        Args:
            key: 查询 key，会自动规范化（lower + strip）。
            value: 缓存值字典，应包含 "markdown"、"timestamp"、"query" 字段。
        """
        # 始终拷贝，确保不修改调用方数据
        value = dict(value)
        if "timestamp" not in value:
            value["timestamp"] = time.monotonic()

        normalized = self._normalize_key(key)

        with self._lock:
            # 如果 key 已存在，更新并移到队尾
            if normalized in self._cache:
                self._cache[normalized] = value
                self._cache.move_to_end(normalized)
                return

            # 自动缩容：先淘汰过期条目
            self._evict_expired()

            # 如果仍然已满，淘汰最久未使用的
            while len(self._cache) >= self._max_size:
                self._evict_lru()

            self._cache[normalized] = value

    def clear(self) -> None:
        """清空所有缓存条目和统计信息。"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> dict[str, int]:
        """返回缓存统计信息。

        Returns:
            包含 size, hits, misses, evictions, max_size, ttl_seconds 的字典。
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "max_size": self._max_size,
                "ttl_seconds": self._ttl_seconds,
            }

    def __len__(self) -> int:
        """返回当前缓存条目数。"""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """检查 key 是否在缓存中且未过期。"""
        normalized = self._normalize_key(key)
        with self._lock:
            if normalized not in self._cache:
                return False
            value = self._cache[normalized]
            if self._is_expired(value):
                return False
            return True
