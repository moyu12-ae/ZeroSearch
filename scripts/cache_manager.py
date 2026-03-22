"""
UnifiedCacheManager - 统一缓存管理器

Phase 9 新增功能

设计要点:
1. 缓存位置: {project}/.cache/zero-search/
   - 使用调用者工作目录，而非 Skills 所在目录
   - Skills 移动后缓存不丢失

2. 惰性清理 (Lazy Cleanup)
   - 不开独立定时器
   - 在 Skills 被调用时顺手检查
   - 每 N 次调用才检查一次

3. 固定容量 FIFO
   - 使用 deque(maxlen=N)
   - 超出自动丢弃最旧数据

4. 缓冲批量写入
   - 凑够 N 条才写磁盘
   - 减少 IO 次数
"""

import os
import json
import time
import atexit
from pathlib import Path
from collections import deque
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """缓存配置"""
    name: str
    max_entries: int = 1000
    max_size_mb: float = 10.0
    buffer_size: int = 50
    cleanup_ratio: float = 0.5
    check_interval: int = 10


class UnifiedCacheManager:
    """
    统一缓存管理器

    特性:
    - 项目级缓存目录
    - 惰性清理
    - 固定容量
    - 缓冲写入

    使用示例:
        cache = UnifiedCacheManager("performance")

        # 记录数据
        cache.append({"query": "test", "duration": 1.5})

        # 获取统计
        stats = cache.get_stats()

        # 获取最近数据
        recent = cache.get_recent(100)
    """

    CACHE_ROOT = ".cache"
    CACHE_SUB_DIR = "zero-search"

    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache_dir = self._get_cache_dir()
        self._cache_file = self._cache_dir / f"{config.name}.jsonl"
        self._buffer: List[Dict[str, Any]] = []
        self._check_counter = 0
        self._initialized = False

        self._ensure_dir()
        self._register_atexit()
        self._initialized = True

    @staticmethod
    def _get_cache_dir() -> Path:
        """
        获取项目级缓存目录

        使用调用者的工作目录，而非 Skills 所在目录
        这样 Skills 移动时缓存不会丢失
        """
        project_root = Path(os.getcwd())
        return project_root / UnifiedCacheManager.CACHE_ROOT / UnifiedCacheManager.CACHE_SUB_DIR

    def _ensure_dir(self):
        """确保缓存目录存在"""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _register_atexit(self):
        """注册程序退出时刷新缓存"""
        atexit.register(self.flush)

    def lazy_cleanup_if_needed(self):
        """
        惰性清理检查

        每次 Skills 被调用时检查，每 N 次调用才真正检查
        设计要点:
        - 不是每次都检查（减少开销）
        - 只在超过阈值时才清理
        """
        if not self._initialized:
            return

        self._check_counter += 1

        if self._check_counter < self.config.check_interval:
            return

        self._check_counter = 0
        self._perform_lazy_cleanup()

    def _perform_lazy_cleanup(self):
        """执行惰性清理"""
        if not self._cache_file.exists():
            return

        try:
            size_mb = self._cache_file.stat().st_size / (1024 * 1024)

            if size_mb > self.config.max_size_mb:
                self._trim_to_half()

            lines = self._cache_file.read_text().strip().split('\n')
            if len(lines) > self.config.max_entries:
                self._trim_to_half()

        except Exception:
            pass

    def _trim_to_half(self):
        """保留一半数据"""
        if not self._cache_file.exists():
            return

        try:
            lines = self._cache_file.read_text().strip().split('\n')
            if not lines or lines == ['']:
                return

            keep_count = max(1, int(len(lines) * self.config.cleanup_ratio))
            kept_lines = lines[-keep_count:]

            self._cache_file.write_text('\n'.join(kept_lines) + '\n')

        except Exception:
            pass

    def append(self, data: Dict[str, Any]):
        """
        追加数据到缓存

        Args:
            data: 要缓存的数据字典
        """
        self._buffer.append(data)

        if len(self._buffer) >= self.config.buffer_size:
            self.flush()

    def flush(self):
        """
        批量写入缓存到磁盘

        只有在缓冲区有数据时才写入
        """
        if not self._buffer:
            return

        try:
            self._ensure_dir()
            with open(self._cache_file, 'a', encoding='utf-8') as f:
                for item in self._buffer:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        except Exception:
            pass

        self._buffer.clear()

    def get_recent(self, n: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的 N 条数据

        Args:
            n: 要获取的条数

        Returns:
            最近 N 条数据的列表
        """
        if not self._cache_file.exists():
            return []

        try:
            lines = self._cache_file.read_text().strip().split('\n')
            recent_lines = lines[-n:] if lines else []

            return [
                json.loads(line)
                for line in recent_lines
                if line.strip()
            ]
        except Exception:
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        size_mb = 0.0
        entry_count = 0

        if self._cache_file.exists():
            try:
                size_mb = self._cache_file.stat().st_size / (1024 * 1024)
                lines = self._cache_file.read_text().strip().split('\n')
                entry_count = len([l for l in lines if l.strip()])
            except Exception:
                pass

        return {
            "name": self.config.name,
            "cache_dir": str(self._cache_dir),
            "cache_file": str(self._cache_file),
            "size_mb": round(size_mb, 2),
            "entry_count": entry_count,
            "max_entries": self.config.max_entries,
            "max_size_mb": self.config.max_size_mb,
            "buffer_pending": len(self._buffer),
            "check_interval": self.config.check_interval,
        }

    def clear(self):
        """
        清空所有缓存数据
        """
        self._buffer.clear()

        if self._cache_file.exists():
            try:
                self._cache_file.unlink()
            except Exception:
                pass

    def get_cache_path(self) -> str:
        """
        获取缓存文件路径

        Returns:
            缓存文件的绝对路径
        """
        return str(self._cache_file.absolute())


def create_cache(
    name: str,
    max_entries: int = 1000,
    max_size_mb: float = 10.0,
    buffer_size: int = 50,
    cleanup_ratio: float = 0.5,
    check_interval: int = 10,
) -> UnifiedCacheManager:
    """
    创建缓存管理器的便捷工厂函数

    Args:
        name: 缓存名称
        max_entries: 最大条目数
        max_size_mb: 最大文件大小 (MB)
        buffer_size: 缓冲大小
        cleanup_ratio: 清理时保留比例
        check_interval: 检查间隔

    Returns:
        UnifiedCacheManager 实例
    """
    config = CacheConfig(
        name=name,
        max_entries=max_entries,
        max_size_mb=max_size_mb,
        buffer_size=buffer_size,
        cleanup_ratio=cleanup_ratio,
        check_interval=check_interval,
    )
    return UnifiedCacheManager(config)


def demo():
    """演示 UnifiedCacheManager 的使用"""
    print("=" * 60)
    print("UnifiedCacheManager 演示 - Phase 9")
    print("=" * 60)

    cache = create_cache(
        name="demo",
        max_entries=100,
        max_size_mb=1.0,
        buffer_size=10,
    )

    print(f"\n[1] 缓存位置:")
    stats = cache.get_stats()
    print(f"   缓存目录: {stats['cache_dir']}")
    print(f"   缓存文件: {stats['cache_file']}")

    print(f"\n[2] 追加 5 条数据 (缓冲大小=10，不会立即写入):")
    for i in range(5):
        cache.append({
            "id": i,
            "query": f"test_query_{i}",
            "duration": 1.0 + i * 0.1,
            "timestamp": time.time(),
        })
        print(f"   - 添加数据 {i}")

    stats = cache.get_stats()
    print(f"\n   缓冲区待写入: {stats['buffer_pending']}")

    print(f"\n[3] 强制刷新 (追加 5 条达到缓冲上限):")
    for i in range(5, 10):
        cache.append({
            "id": i,
            "query": f"test_query_{i}",
            "duration": 1.0 + i * 0.1,
            "timestamp": time.time(),
        })

    stats = cache.get_stats()
    print(f"   刷新后缓冲区: {stats['buffer_pending']}")
    print(f"   当前条目数: {stats['entry_count']}")

    print(f"\n[4] 获取最近 3 条数据:")
    recent = cache.get_recent(3)
    for item in recent:
        print(f"   - id={item['id']}, query={item['query']}")

    print(f"\n[5] 获取统计信息:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"\n[6] 清理缓存:")
    cache.clear()
    stats = cache.get_stats()
    print(f"   清理后条目数: {stats['entry_count']}")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
