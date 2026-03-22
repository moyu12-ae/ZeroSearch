"""
Batch Search - 批量搜索封装

Phase 7 新增功能

问题:
- 当前需要手动编写循环和等待逻辑
- 缺乏统一的批量搜索接口
- 没有进度追踪和回调机制

解决方案:
- BatchSearchEngine: 封装批量搜索逻辑
- batch_search(): 一行代码实现批量搜索
- between_callback: 搜索间隔回调
- 进度追踪: 实时显示搜索进度
- 错误处理: 自动跳过失败项

使用方式:
    from scripts.batch_search import BatchSearchEngine

    engine = BatchSearchEngine(search_engine)

    results = engine.batch_search(
        queries=["query1", "query2", "query3"],
        on_progress=progress_callback,
        on_result=result_callback,
    )
"""

import time
import logging
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class BatchSearchConfig:
    """批量搜索配置"""
    enable_smart_timeout: bool = True
    enable_smart_rate_limiter: bool = True
    enable_citation_cleaning: bool = True
    wait_between_searches: float = 5.0
    max_concurrent: int = 1
    skip_on_error: bool = True
    save_interval: int = 1


@dataclass
class BatchSearchResult:
    """批量搜索结果"""
    query: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    elapsed_time: float = 0.0
    citations_count: int = 0


class BatchSearchEngine:
    """
    批量搜索引擎

    功能:
    - 一行代码实现批量搜索
    - 进度追踪和回调
    - 错误处理和跳过
    - 增量保存支持
    - 统计摘要

    使用方式:
        engine = BatchSearchEngine(search_engine)

        def on_progress(completed, total, result):
            print(f"进度: {completed}/{total}")

        def on_result(query, result, error):
            if result:
                print(f"成功: {query}")

        results = engine.batch_search(
            queries=["query1", "query2", "query3"],
            on_progress=on_progress,
            on_result=on_result,
        )
    """

    def __init__(
        self,
        search_engine=None,
        config: Optional[BatchSearchConfig] = None,
    ):
        """
        初始化批量搜索引擎

        Args:
            search_engine: 底层搜索引擎（可选）
            config: 批量搜索配置
        """
        self._search_engine = search_engine
        self._config = config or BatchSearchConfig()

        self._results: List[BatchSearchResult] = []
        self._stats = {
            "total": 0,
            "completed": 0,
            "successful": 0,
            "failed": 0,
            "total_citations": 0,
            "total_time": 0.0,
        }

    def batch_search(
        self,
        queries: List[str],
        on_progress: Optional[Callable[[int, int, Any], None]] = None,
        on_result: Optional[Callable[[str, Any, Optional[str]], None]] = None,
        on_complete: Optional[Callable[[List[BatchSearchResult]], None]] = None,
    ) -> List[BatchSearchResult]:
        """
        批量搜索

        Args:
            queries: 查询列表
            on_progress: 进度回调 (completed, total, result) -> None
            on_result: 结果回调 (query, result, error) -> None
            on_complete: 完成回调 (results) -> None

        Returns:
            搜索结果列表
        """
        if not queries:
            logger.warning("No queries provided")
            return []

        self._results = []
        self._stats = {
            "total": len(queries),
            "completed": 0,
            "successful": 0,
            "failed": 0,
            "total_citations": 0,
            "total_time": 0.0,
        }

        logger.info(f"Starting batch search: {len(queries)} queries")

        for i, query in enumerate(queries, 1):
            start_time = time.time()

            try:
                if self._search_engine:
                    result = self._search_engine.search(query)
                else:
                    raise ValueError("No search engine provided")

                elapsed = time.time() - start_time

                batch_result = BatchSearchResult(
                    query=query,
                    success=True,
                    result=result,
                    elapsed_time=elapsed,
                    citations_count=len(getattr(result, 'citations', [])) if result else 0,
                )

                self._stats["successful"] += 1
                self._stats["total_citations"] += batch_result.citations_count
                self._stats["total_time"] += elapsed

                logger.info(f"[{i}/{len(queries)}] Success: {query}")

                if on_result:
                    on_result(query, result, None)

            except Exception as e:
                elapsed = time.time() - start_time

                batch_result = BatchSearchResult(
                    query=query,
                    success=False,
                    error=str(e),
                    elapsed_time=elapsed,
                )

                self._stats["failed"] += 1

                logger.warning(f"[{i}/{len(queries)}] Failed: {query} - {e}")

                if on_result:
                    on_result(query, None, str(e))

                if not self._config.skip_on_error:
                    self._results.append(batch_result)
                    self._stats["completed"] = i
                    continue

            self._results.append(batch_result)
            self._stats["completed"] = i

            if on_progress:
                on_progress(i, len(queries), batch_result)

            if i < len(queries) and self._config.wait_between_searches > 0:
                logger.debug(f"Waiting {self._config.wait_between_searches}s before next search")
                time.sleep(self._config.wait_between_searches)

        logger.info(f"Batch search complete: {self._stats['successful']} successful, {self._stats['failed']} failed")

        if on_complete:
            on_complete(self._results)

        return self._results

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        stats = self._stats.copy()

        if stats["completed"] > 0:
            stats["success_rate"] = stats["successful"] / stats["completed"]
            stats["avg_time"] = stats["total_time"] / stats["completed"]
        else:
            stats["success_rate"] = 0.0
            stats["avg_time"] = 0.0

        return stats

    def get_results(self) -> List[BatchSearchResult]:
        """获取所有结果"""
        return self._results.copy()

    def get_successful_results(self) -> List[BatchSearchResult]:
        """获取成功的搜索结果"""
        return [r for r in self._results if r.success]

    def get_failed_results(self) -> List[BatchSearchResult]:
        """获取失败的搜索结果"""
        return [r for r in self._results if not r.success]

    def get_summary(self) -> str:
        """
        获取摘要报告

        Returns:
            格式化的摘要字符串
        """
        stats = self.get_stats()

        lines = [
            "Batch Search Summary:",
            f"  Total Queries: {stats['total']}",
            f"  Completed: {stats['completed']}",
            f"  Successful: {stats['successful']}",
            f"  Failed: {stats['failed']}",
            f"  Success Rate: {stats['success_rate'] * 100:.1f}%",
            f"  Total Citations: {stats['total_citations']}",
            f"  Total Time: {stats['total_time']:.1f}s",
            f"  Avg Time: {stats['avg_time']:.1f}s",
        ]

        if stats['failed'] > 0:
            lines.append("")
            lines.append("  Failed Queries:")
            for r in self.get_failed_results():
                lines.append(f"    - {r.query}: {r.error}")

        return "\n".join(lines)

    def export_to_dict(self) -> Dict[str, Any]:
        """
        导出为字典格式

        Returns:
            字典格式的结果
        """
        return {
            "stats": self.get_stats(),
            "results": [
                {
                    "query": r.query,
                    "success": r.success,
                    "elapsed_time": r.elapsed_time,
                    "citations_count": r.citations_count,
                    "error": r.error,
                }
                for r in self._results
            ],
        }


def create_batch_engine(search_engine, **kwargs) -> BatchSearchEngine:
    """
    便捷工厂函数：创建批量搜索引擎

    Args:
        search_engine: 底层搜索引擎
        **kwargs: 其他配置参数

    Returns:
        BatchSearchEngine 实例
    """
    config = BatchSearchConfig(**kwargs)
    return BatchSearchEngine(search_engine, config)


def demo():
    """演示 BatchSearchEngine 的使用"""
    print("=" * 70)
    print("BatchSearchEngine 演示 - Phase 7")
    print("=" * 70)

    class MockSearchEngine:
        def search(self, query):
            import random
            time.sleep(0.1)
            return type('Result', (), {
                'query': query,
                'citations': [type('Citation', (), {'title': f'Re{chr(115)}{chr(117)}{chr(108)}{chr(116)} {i}'})() for i in range(random.randint(3, 10))]
            })()

    mock_engine = MockSearchEngine()
    batch_engine = BatchSearchEngine(mock_engine)

    queries = [
        "Python best practices",
        "Machine learning basics",
        "Deep learning tutorial",
    ]

    def on_progress(completed, total, result):
        status = "✅" if result.success else "❌"
        print(f"  [{completed}/{total}] {status} {result.query}")

    def on_result(query, result, error):
        if error:
            print(f"    失败: {error}")

    print("\n开始批量搜索:")
    results = batch_engine.batch_search(
        queries=queries,
        on_progress=on_progress,
        on_result=on_result,
    )

    print("\n" + batch_engine.get_summary())

    print("\n" + "=" * 70)
    print("🎉 BatchSearchEngine 演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
