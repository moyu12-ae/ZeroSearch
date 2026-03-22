#!/usr/bin/env python3
"""
Cache CLI - 缓存管理命令行工具

Phase 9 新增功能

功能:
- 查看缓存统计
- 手动清理缓存
- 查看缓存位置
- 导出缓存数据
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cache_manager import create_cache, UnifiedCacheManager, CacheConfig
from performance_monitor import PerformanceMonitor, create_performance_monitor


def cmd_stats(args):
    """查看缓存统计"""
    print("\n" + "=" * 60)
    print("📊 缓存统计")
    print("=" * 60)

    cache_names = ["performance", "timeout", "rate_limit"]
    total_size = 0

    for name in cache_names:
        try:
            config = CacheConfig(name=name)
            cache = UnifiedCacheManager(config)

            stats = cache.get_stats()
            if stats['entry_count'] > 0 or stats['size_mb'] > 0:
                print(f"\n📁 {name}:")
                print(f"   位置: {stats['cache_dir']}")
                print(f"   条目: {stats['entry_count']} / {stats['max_entries']}")
                print(f"   大小: {stats['size_mb']} MB / {stats['max_size_mb']} MB")
                total_size += stats['size_mb']
        except Exception as e:
            print(f"\n📁 {name}: (未找到)")
            continue

    print(f"\n💾 缓存总大小: {total_size:.2f} MB")
    print("=" * 60)


def cmd_path(args):
    """查看缓存路径"""
    cache = create_cache("performance")
    print(f"\n📂 缓存根目录:")
    print(f"   {cache._cache_dir}")
    print(f"\n📄 缓存文件:")
    print(f"   {cache._cache_file}")


def cmd_clean(args):
    """清理缓存"""
    cache_names = args.cache.split(",") if args.cache else ["performance", "timeout", "rate_limit"]

    print("\n" + "=" * 60)
    print("🧹 清理缓存")
    print("=" * 60)

    for name in cache_names:
        name = name.strip()
        try:
            config = CacheConfig(name=name)
            cache = UnifiedCacheManager(config)

            stats = cache.get_stats()
            if stats['entry_count'] > 0:
                cache.clear()
                print(f"   ✅ {name}: 已清理 ({stats['entry_count']} 条)")
            else:
                print(f"   ⏭️  {name}: 无数据")
        except Exception as e:
            print(f"   ❌ {name}: 清理失败 - {e}")

    print("=" * 60)
    print("清理完成!")


def cmd_export(args):
    """导出缓存数据"""
    cache = create_performance_monitor()

    output_file = args.output or "cache_export.json"
    recent = cache.get_recent_metrics(args.limit)

    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([m.to_dict() for m in recent], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已导出 {len(recent)} 条记录到: {output_file}")


def cmd_monitor(args):
    """显示性能监控面板"""
    monitor = create_performance_monitor()
    monitor.print_dashboard()


def main():
    parser = argparse.ArgumentParser(
        description="缓存管理命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cache_cli.py stats       # 查看缓存统计
  python cache_cli.py path       # 查看缓存路径
  python cache_cli.py clean       # 清理所有缓存
  python cache_cli.py clean --cache performance  # 只清理 performance
  python cache_cli.py export      # 导出性能数据
  python cache_cli.py monitor     # 显示性能监控面板
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    subparsers.add_parser("stats", help="查看缓存统计")

    subparsers.add_parser("path", help="查看缓存路径")

    clean_parser = subparsers.add_parser("clean", help="清理缓存")
    clean_parser.add_argument(
        "--cache",
        type=str,
        default=None,
        help="指定要清理的缓存（逗号分隔，如 'performance,timeout'）"
    )

    export_parser = subparsers.add_parser("export", help="导出缓存数据")
    export_parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出文件路径"
    )
    export_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=1000,
        help="导出条数限制"
    )

    subparsers.add_parser("monitor", help="显示性能监控面板")

    args = parser.parse_args()

    if args.command == "stats":
        cmd_stats(args)
    elif args.command == "path":
        cmd_path(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "monitor":
        cmd_monitor(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
