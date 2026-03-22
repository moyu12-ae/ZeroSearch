"""
Incremental Saver - 增量保存和断点续传

Phase 7 新增功能

问题:
- 当前只在最后一次性保存结果
- 中途失败会丢失所有数据
- 无法从中断点继续

解决方案:
- 增量保存：每次搜索后立即保存
- 断点续传：中断后可从断点继续
- 状态持久化：保存搜索进度和结果
- 异步保存：不阻塞搜索流程

使用方式:
    from scripts.incremental_saver import IncrementalSaver

    saver = IncrementalSaver(output_file="research_results.json")

    # 保存单个结果
    saver.save_result(search_result)

    # 保存所有结果
    saver.save_all_results(results)

    # 加载已有结果（断点续传）
    existing_results = saver.load_results()
"""

import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class SearchResultRecord:
    """搜索结果记录"""
    query: str
    timestamp: str
    success: bool
    elapsed_time: float
    citations_count: int = 0
    ai_mode_available: bool = False
    url: str = ""
    summary: str = ""
    error_message: str = ""
    citations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResultRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SaverState:
    """保存器状态"""
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    last_save_time: str = ""
    version: str = "1.0.0"
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaverState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class IncrementalSaver:
    """
    增量保存器

    功能:
    - 增量保存：每次搜索后立即保存
    - 断点续传：中断后可从断点继续
    - 状态追踪：记录搜索进度
    - 格式兼容：支持新旧格式

    使用方式:
        saver = IncrementalSaver("results.json")

        # 搜索前：加载已有结果
        existing = saver.load_results()

        # 搜索后：增量保存
        saver.save_result(result)

        # 获取当前进度
        progress = saver.get_progress()
    """

    def __init__(
        self,
        output_file: str = "research_results.json",
        auto_save: bool = True,
        save_interval: int = 1,
    ):
        """
        初始化增量保存器

        Args:
            output_file: 输出文件路径
            auto_save: 是否自动保存
            save_interval: 保存间隔（每次搜索后保存）
        """
        self.output_file = Path(output_file)
        self.auto_save = auto_save
        self.save_interval = save_interval

        self._results: List[SearchResultRecord] = []
        self._state = SaverState()
        self._is_dirty = False

        self._load_existing()

    def _load_existing(self):
        """加载已有结果（断点续传）"""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    if 'results' in data:
                        self._results = [
                            SearchResultRecord.from_dict(r)
                            for r in data['results']
                        ]
                    if 'state' in data:
                        self._state = SaverState.from_dict(data['state'])

                    logger.info(f"Loaded {len(self._results)} existing results")
                elif isinstance(data, list):
                    self._results = [
                        SearchResultRecord.from_dict(r)
                        for r in data
                    ]
                    logger.info(f"Loaded {len(self._results)} existing results (legacy format)")

                self._update_state()

            except Exception as e:
                logger.warning(f"Failed to load existing results: {e}")
                self._results = []
                self._state = SaverState()

        else:
            self._state.created_at = datetime.now().isoformat()
            logger.info("No existing results found, starting fresh")

    def _update_state(self):
        """更新状态"""
        self._state.total_searches = len(self._results)
        self._state.successful_searches = sum(1 for r in self._results if r.success)
        self._state.failed_searches = sum(1 for r in self._results if not r.success)
        self._state.last_save_time = datetime.now().isoformat()
        self._state.updated_at = datetime.now().isoformat()

    def save_result(self, result: Any, query: str = "", elapsed_time: float = 0.0) -> bool:
        """
        保存单个搜索结果

        Args:
            result: 搜索结果对象或字典
            query: 搜索查询
            elapsed_time: 搜索耗时

        Returns:
            是否保存成功
        """
        try:
            if isinstance(result, dict):
                record = SearchResultRecord(
                    query=query or result.get('query', ''),
                    timestamp=datetime.now().isoformat(),
                    success=result.get('success', True),
                    elapsed_time=elapsed_time,
                    citations_count=len(result.get('citations', [])),
                    ai_mode_available=result.get('ai_mode_available', False),
                    url=result.get('url', ''),
                    summary=result.get('summary', ''),
                    error_message=result.get('error_message', ''),
                    citations=[
                        {
                            'title': c.get('title', ''),
                            'url': c.get('url', ''),
                            'context': c.get('context', ''),
                        }
                        for c in result.get('citations', [])
                    ],
                )
            else:
                record = SearchResultRecord(
                    query=query or getattr(result, 'query', ''),
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    elapsed_time=elapsed_time,
                    citations_count=len(getattr(result, 'citations', [])),
                    ai_mode_available=getattr(result, 'ai_mode_available', False),
                    url=getattr(result, 'url', ''),
                    summary=getattr(result, 'summary', ''),
                    citations=[
                        {
                            'title': getattr(c, 'title', ''),
                            'url': getattr(c, 'url', ''),
                            'context': getattr(c, 'context', ''),
                        }
                        for c in getattr(result, 'citations', [])
                    ],
                )

            self._results.append(record)
            self._is_dirty = True
            self._update_state()

            if self.auto_save:
                self.save_all_results()

            logger.debug(f"Saved result for query: {record.query}")
            return True

        except Exception as e:
            logger.error(f"Failed to save result: {e}")
            return False

    def save_all_results(self) -> bool:
        """
        保存所有结果到文件

        Returns:
            是否保存成功
        """
        if not self._is_dirty and self.output_file.exists():
            logger.debug("No changes to save")
            return True

        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'version': self._state.version,
                'created_at': self._state.created_at,
                'updated_at': self._state.updated_at,
                'state': self._state.to_dict(),
                'results': [r.to_dict() for r in self._results],
            }

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._is_dirty = False
            logger.info(f"Saved {len(self._results)} results to {self.output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False

    def load_results(self) -> List[SearchResultRecord]:
        """
        加载已有结果（用于断点续传）

        Returns:
            已有的搜索结果列表
        """
        return self._results.copy()

    def get_progress(self) -> Dict[str, Any]:
        """
        获取当前进度

        Returns:
            进度信息字典
        """
        return {
            'total': self._state.total_searches,
            'successful': self._state.successful_searches,
            'failed': self._state.failed_searches,
            'success_rate': (
                self._state.successful_searches / self._state.total_searches
                if self._state.total_searches > 0
                else 0.0
            ),
            'last_save': self._state.last_save_time,
        }

    def get_failed_queries(self) -> List[str]:
        """
        获取失败的查询列表（用于重试）

        Returns:
            失败查询列表
        """
        return [r.query for r in self._results if not r.success]

    def get_successful_results(self) -> List[SearchResultRecord]:
        """
        获取成功的搜索结果

        Returns:
            成功结果列表
        """
        return [r for r in self._results if r.success]

    def clear_results(self) -> bool:
        """
        清除所有结果（谨慎使用）

        Returns:
            是否清除成功
        """
        try:
            self._results = []
            self._state = SaverState()
            self._state.created_at = datetime.now().isoformat()
            self._is_dirty = True
            self.save_all_results()
            logger.info("Cleared all results")
            return True
        except Exception as e:
            logger.error(f"Failed to clear results: {e}")
            return False

    def export_to_markdown(self, output_file: str = "research_results.md") -> bool:
        """
        导出为 Markdown 格式

        Args:
            output_file: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            lines = [
                "# Research Results",
                "",
                f"**Generated**: {self._state.created_at}",
                f"**Updated**: {self._state.updated_at}",
                "",
                "## Progress",
                "",
                f"- Total Searches: {self._state.total_searches}",
                f"- Successful: {self._state.successful_searches}",
                f"- Failed: {self._state.failed_searches}",
                "",
                "## Results",
                "",
            ]

            for i, result in enumerate(self._results, 1):
                status = "✅" if result.success else "❌"
                lines.append(f"### {i}. {status} {result.query}")
                lines.append("")
                lines.append(f"**Time**: {result.elapsed_time:.1f}s")
                lines.append(f"**Citations**: {result.citations_count}")
                if result.summary:
                    lines.append("")
                    lines.append(f"**Summary**: {result.summary[:200]}...")
                if result.citations:
                    lines.append("")
                    lines.append("**Citations**:")
                    for c in result.citations[:5]:
                        lines.append(f"- [{c.get('title', 'N/A')}]({c.get('url', '')})")
                lines.append("")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            logger.info(f"Exported results to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to markdown: {e}")
            return False


def demo():
    """演示 IncrementalSaver 的使用"""
    print("=" * 70)
    print("IncrementalSaver 演示 - Phase 7")
    print("=" * 70)

    saver = IncrementalSaver("demo_results.json")

    print("\n[1] 加载已有结果")
    existing = saver.load_results()
    print(f"已有结果: {len(existing)} 条")

    print("\n[2] 模拟保存结果")
    mock_results = [
        {
            'query': 'Python best practices',
            'success': True,
            'elapsed_time': 5.2,
            'citations_count': 10,
            'ai_mode_available': True,
            'url': 'https://example.com/1',
            'summary': 'Python best practices guide...',
            'citations': [
                {'title': 'Python Guide', 'url': 'https://example.com/py'},
                {'title': 'Best Practices', 'url': 'https://example.com/bp'},
            ],
        },
        {
            'query': 'Machine learning basics',
            'success': True,
            'elapsed_time': 8.1,
            'citations_count': 15,
            'ai_mode_available': True,
            'url': 'https://example.com/2',
            'summary': 'Machine learning fundamentals...',
            'citations': [],
        },
    ]

    for result in mock_results:
        saver.save_result(result)
        print(f"  保存: {result['query']}")

    print("\n[3] 获取进度")
    progress = saver.get_progress()
    print(f"总搜索: {progress['total']}")
    print(f"成功: {progress['successful']}")
    print(f"失败: {progress['failed']}")
    print(f"成功率: {progress['success_rate']*100:.1f}%")

    print("\n[4] 导出 Markdown")
    saver.export_to_markdown("demo_results.md")
    print("已导出: demo_results.md")

    print("\n" + "=" * 70)
    print("🎉 IncrementalSaver 演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
