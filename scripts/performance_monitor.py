"""
Performance Monitor - 性能监控面板

Phase 8 新增功能
Phase 9 重构: 使用 UnifiedCacheManager

功能:
- 实时统计搜索性能
- 历史数据对比
- 性能趋势分析
- CLI 界面展示

Phase 9 改进:
- 使用 UnifiedCacheManager 替代直接文件操作
- 惰性清理机制
- 固定容量缓存
- 缓冲批量写入
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from .cache_manager import create_cache, UnifiedCacheManager, CacheConfig
except ImportError:
    from cache_manager import create_cache, UnifiedCacheManager, CacheConfig


@dataclass
class SearchMetric:
    """搜索指标"""
    timestamp: str
    query: str
    duration: float
    success: bool
    citations_count: int
    ai_mode_available: bool
    error_type: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "query": self.query,
            "duration": self.duration,
            "success": self.success,
            "citations_count": self.citations_count,
            "ai_mode_available": self.ai_mode_available,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchMetric":
        return cls(
            timestamp=data.get("timestamp", ""),
            query=data.get("query", ""),
            duration=data.get("duration", 0.0),
            success=data.get("success", False),
            citations_count=data.get("citations_count", 0),
            ai_mode_available=data.get("ai_mode_available", False),
            error_type=data.get("error_type", ""),
            error_message=data.get("error_message", ""),
        )


class PerformanceMonitor:
    """
    性能监控面板

    Phase 9 改进:
    - 使用 UnifiedCacheManager 统一缓存管理
    - 惰性清理机制 (每 N 次调用检查一次)
    - 固定容量缓存
    - 缓冲批量写入

    功能:
    - 记录每次搜索的性能指标
    - 统计成功率、平均耗时等
    - 支持历史数据导出
    - CLI 风格输出
    """

    DEFAULT_CONFIG = CacheConfig(
        name="performance",
        max_entries=1000,
        max_size_mb=10.0,
        buffer_size=50,
        cleanup_ratio=0.5,
        check_interval=10,
    )

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        cache_manager: Optional[UnifiedCacheManager] = None,
    ):
        """
        初始化监控器

        Args:
            config: 缓存配置
            cache_manager: 可选的自定义缓存管理器
        """
        self._config = config or self.DEFAULT_CONFIG

        if cache_manager:
            self._cache = cache_manager
        else:
            self._cache = UnifiedCacheManager(self._config)

    def _lazy_cleanup(self):
        """
        惰性清理检查

        每次 record_search 时调用，每 N 次调用才真正检查
        """
        self._cache.lazy_cleanup_if_needed()

    def record_search(
        self,
        query: str,
        duration: float,
        success: bool,
        citations_count: int = 0,
        ai_mode_available: bool = False,
        error_type: str = "",
        error_message: str = "",
    ):
        """
        记录搜索指标

        Args:
            query: 搜索查询
            duration: 搜索耗时（秒）
            success: 是否成功
            citations_count: 引用数量
            ai_mode_available: AI Mode 是否可用
            error_type: 错误类型
            error_message: 错误消息
        """
        self._lazy_cleanup()

        metric = SearchMetric(
            timestamp=datetime.now().isoformat(),
            query=query,
            duration=duration,
            success=success,
            citations_count=citations_count,
            ai_mode_available=ai_mode_available,
            error_type=error_type,
            error_message=error_message,
        )

        self._cache.append(metric.to_dict())

    def get_recent_metrics(self, n: int = 100) -> List[SearchMetric]:
        """
        获取最近的 N 条指标

        Args:
            n: 要获取的条数

        Returns:
            SearchMetric 列表
        """
        recent = self._cache.get_recent(n)
        return [SearchMetric.from_dict(item) for item in recent]

    def get_summary(self) -> Dict[str, Any]:
        """
        获取统计摘要

        Returns:
            统计字典
        """
        recent = self.get_recent_metrics(1000)

        if not recent:
            return {
                "total_searches": 0,
                "successful_searches": 0,
                "failed_searches": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "total_citations": 0,
                "avg_citations": 0.0,
            }

        total = len(recent)
        successful = sum(1 for m in recent if m.success)
        failed = total - successful
        durations = [m.duration for m in recent]
        citations = [m.citations_count for m in recent if m.citations_count > 0]

        return {
            "total_searches": total,
            "successful_searches": successful,
            "failed_searches": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_duration": sum(durations) / len(durations) if durations else 0.0,
            "min_duration": min(durations) if durations else 0.0,
            "max_duration": max(durations) if durations else 0.0,
            "total_citations": sum(citations),
            "avg_citations": sum(citations) / len(citations) if citations else 0.0,
        }

    def get_trends(self, window: int = 10) -> Dict[str, Any]:
        """
        获取性能趋势

        Args:
            window: 窗口大小

        Returns:
            趋势字典
        """
        recent = self.get_recent_metrics(window)

        if not recent:
            return {
                "window": window,
                "recent_success_rate": 0.0,
                "recent_avg_duration": 0.0,
                "trend": "stable",
            }

        recent_success = sum(1 for m in recent if m.success)
        recent_durations = [m.duration for m in recent]

        all_metrics = self.get_recent_metrics(window * 2)

        trend = "stable"
        if len(all_metrics) >= window * 2:
            previous = all_metrics[-window * 2:-window] if len(all_metrics) >= window * 2 else all_metrics[:-window]
            if previous:
                prev_avg = sum(m.duration for m in previous) / len(previous)
                curr_avg = sum(recent_durations) / len(recent_durations)
                if curr_avg < prev_avg * 0.9:
                    trend = "improving"
                elif curr_avg > prev_avg * 1.1:
                    trend = "degrading"

        return {
            "window": window,
            "recent_success_rate": recent_success / len(recent),
            "recent_avg_duration": sum(recent_durations) / len(recent_durations),
            "trend": trend,
        }

    def print_dashboard(self):
        """打印监控面板"""
        summary = self.get_summary()
        trends = self.get_trends()

        print("\n" + "=" * 60)
        print("📊 Performance Monitor Dashboard")
        print("=" * 60)

        print(f"\n📈 Overview:")
        print(f"   Total Searches:    {summary['total_searches']}")
        print(f"   Successful:        {summary['successful_searches']}")
        print(f"   Failed:            {summary['failed_searches']}")
        print(f"   Success Rate:      {summary['success_rate']*100:.1f}%")

        print(f"\n⏱️  Performance:")
        print(f"   Avg Duration:      {summary['avg_duration']:.1f}s")
        print(f"   Min Duration:      {summary['min_duration']:.1f}s")
        print(f"   Max Duration:      {summary['max_duration']:.1f}s")

        print(f"\n📚 Citations:")
        print(f"   Total:             {summary['total_citations']}")
        print(f"   Avg per Search:    {summary['avg_citations']:.1f}")

        print(f"\n📉 Trend (last {trends['window']}):")
        trend_emoji = {
            "improving": "✅",
            "degrading": "⚠️",
            "stable": "➡️",
        }
        print(f"   Success Rate:      {trends['recent_success_rate']*100:.1f}%")
        print(f"   Avg Duration:      {trends['recent_avg_duration']:.1f}s")
        print(f"   Status:            {trend_emoji.get(trends['trend'], '➡️')} {trends['trend']}")

        print(f"\n💾 Cache Info:")
        stats = self._cache.get_stats()
        print(f"   Cache Location:    {stats['cache_dir']}")
        print(f"   Entry Count:       {stats['entry_count']}")
        print(f"   Size:              {stats['size_mb']} MB")

        print("\n" + "=" * 60)

    def export_csv(self, output_file: str = "performance_report.csv"):
        """
        导出 CSV 格式

        Args:
            output_file: 输出文件路径
        """
        import csv

        recent = self.get_recent_metrics(10000)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 'Query', 'Duration', 'Success',
                'Citations', 'AI Mode', 'Error Type', 'Error Message'
            ])

            for m in recent:
                writer.writerow([
                    m.timestamp,
                    m.query,
                    f"{m.duration:.2f}",
                    "Yes" if m.success else "No",
                    m.citations_count,
                    "Yes" if m.ai_mode_available else "No",
                    m.error_type,
                    m.error_message,
                ])

        print(f"\n📄 Exported to: {output_file}")

    def reset(self):
        """重置监控数据"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        return self._cache.get_stats()

    def get_cache_path(self) -> str:
        """
        获取缓存文件路径

        Returns:
            缓存文件绝对路径
        """
        return self._cache.get_cache_path()


def create_performance_monitor(
    max_entries: int = 1000,
    max_size_mb: float = 10.0,
    buffer_size: int = 50,
    check_interval: int = 10,
) -> PerformanceMonitor:
    """
    创建性能监控器的便捷工厂函数

    Args:
        max_entries: 最大条目数
        max_size_mb: 最大文件大小 (MB)
        buffer_size: 缓冲大小
        check_interval: 惰性清理检查间隔

    Returns:
        PerformanceMonitor 实例
    """
    config = CacheConfig(
        name="performance",
        max_entries=max_entries,
        max_size_mb=max_size_mb,
        buffer_size=buffer_size,
        cleanup_ratio=0.5,
        check_interval=check_interval,
    )
    return PerformanceMonitor(config=config)


def demo():
    """演示性能监控面板"""
    print("=" * 60)
    print("Performance Monitor Demo (Phase 9)")
    print("=" * 60)

    monitor = create_performance_monitor(
        max_entries=100,
        max_size_mb=1.0,
        buffer_size=10,
        check_interval=5,
    )

    print(f"\n[1] 缓存位置: {monitor.get_cache_path()}")

    print("\n[2] Recording sample metrics...")
    monitor.record_search(
        query="Python tutorial",
        duration=8.5,
        success=True,
        citations_count=15,
        ai_mode_available=True,
    )

    monitor.record_search(
        query="JavaScript guide",
        duration=12.3,
        success=True,
        citations_count=22,
        ai_mode_available=True,
    )

    monitor.record_search(
        query="React best practices",
        duration=6.8,
        success=True,
        citations_count=18,
        ai_mode_available=True,
    )

    print("\n[3] Printing dashboard...")
    monitor.print_dashboard()

    print("\n[4] Getting trends...")
    trends = monitor.get_trends()
    print(f"Trend: {trends}")

    print("\n[5] Summary:")
    summary = monitor.get_summary()
    print(f"Total searches: {summary['total_searches']}")
    print(f"Success rate: {summary['success_rate']*100:.1f}%")
    print(f"Avg duration: {summary['avg_duration']:.1f}s")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
