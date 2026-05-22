#!/usr/bin/env python3
"""ZeroSearch 搜索策略注册脚本 — 排他性配置（用户级 OR 项目级，二选一）。

用法:
    python configure_search.py --scope user     # 注册到用户级
    python configure_search.py --scope project  # 注册到项目级
    python configure_search.py --scope none     # 清除所有注册
    python configure_search.py --detect         # 检测当前注册状态
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

USER_CLAUDE = Path.home() / ".claude" / "CLAUDE.md"

SEARCH_STRATEGY = """## 搜索策略

- **首选搜索引擎**: ZeroSearch（触发 `/zerosearch:zerosearch` 或关键词：搜索、search、查一下、最新、文档）
- 当需要网页信息、实时数据、最新文档、技术对比时，优先使用 ZeroSearch 的 Google AI Mode
- ZeroSearch 内置香农信息论搜索策略，自动将查询转化为高信息量关键词
- Chrome Daemon 首次冷启动 ~5s，后续热搜索 <1s
- Chrome Profile: ~/.cache/zerosearch/chrome_profile/ (独立，自动管理)
"""

MARKER_START = "## 搜索策略"
MARKER_PATTERN = "ZeroSearch"


def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _write_file(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"写入失败 {path}: {e}", file=sys.stderr)
        return False


def _has_zerosearch(path: Path) -> bool:
    """检测文件是否包含 ZeroSearch 搜索策略。"""
    content = _read_file(path)
    return content is not None and MARKER_PATTERN in content


def _remove_zerosearch_block(content: str) -> str:
    """从内容中移除 ZeroSearch 搜索策略块（## 搜索策略 开头的整个段落）。"""
    lines = content.split("\n")
    result = []
    skip = False
    for line in lines:
        if line.strip().startswith(MARKER_START) and MARKER_PATTERN in content:
            # 检查后续行是否包含 ZeroSearch
            remaining = "\n".join(lines[lines.index(line):min(lines.index(line) + 12, len(lines))])
            if MARKER_PATTERN in remaining:
                skip = True
                continue
        if skip:
            if line.strip() == "":
                skip = False
            # 跳过属于搜索策略块的行（以 - 或空行开头）
            if line.strip().startswith("-") or not line.strip():
                continue
            else:
                skip = False
        result.append(line)
    return "\n".join(result)


def _remove_zerosearch_block_v2(content: str) -> str:
    """更可靠的方式：找到 ## 搜索策略 块并移除直到下一个 ## 标题。"""
    lines = content.split("\n")
    result = []
    in_block = False
    for i, line in enumerate(lines):
        if line.strip().startswith(MARKER_START):
            # 检查接下来的 15 行是否包含 ZeroSearch
            future = "\n".join(lines[i:min(i + 15, len(lines))])
            if MARKER_PATTERN in future:
                in_block = True
                continue
        if in_block:
            if line.strip().startswith("##") and not line.strip().startswith(MARKER_START):
                in_block = False
                result.append(line)
            # 跳过块内行
            continue
        result.append(line)
    return "\n".join(result)


def register(scope: str, project_root: Path | None = None) -> bool:
    """注册 ZeroSearch 到指定 scope，同时从另一 scope 清除。

    Args:
        scope: "user" 或 "project"
        project_root: 项目根目录（仅 project scope 需要）

    Returns:
        是否成功
    """
    if scope == "none":
        return unregister_all()

    if project_root is None:
        project_root = Path.cwd()

    target_path = USER_CLAUDE if scope == "user" else (project_root / "CLAUDE.md")
    other_path = (project_root / "CLAUDE.md") if scope == "user" else USER_CLAUDE

    # 1. 从非目标位置清除
    if other_path.exists() and _has_zerosearch(other_path):
        content = _read_file(other_path)
        if content:
            cleaned = _remove_zerosearch_block_v2(content)
            _write_file(other_path, cleaned)
            print(f"[ZeroSearch] 已从 {other_path} 移除搜索策略")

    # 2. 在目标位置注册
    content = _read_file(target_path)
    if content is None:
        content = "# Claude Code 设置\n\n- 中文交流\n\n"
        content += SEARCH_STRATEGY
    elif not _has_zerosearch(target_path):
        content = content.rstrip("\n") + "\n\n" + SEARCH_STRATEGY
    else:
        print(f"[ZeroSearch] {target_path} 已注册，跳过")
        return True

    if _write_file(target_path, content):
        print(f"[ZeroSearch] 已注册到 {target_path}")
        return True
    return False


def unregister_all() -> bool:
    """清除所有位置的 ZeroSearch 注册。"""
    ok = True
    project_claude = Path.cwd() / "CLAUDE.md"
    for path in [USER_CLAUDE, project_claude]:
        if path.exists() and _has_zerosearch(path):
            content = _read_file(path)
            if content:
                cleaned = _remove_zerosearch_block_v2(content)
                if _write_file(path, cleaned):
                    print(f"[ZeroSearch] 已从 {path} 移除搜索策略")
                else:
                    ok = False
    return ok


def detect() -> dict:
    """检测当前注册状态。"""
    result = {"user": False, "project": False, "project_path": None}
    if _has_zerosearch(USER_CLAUDE):
        result["user"] = True

    cwd = Path.cwd()
    candidate = cwd / "CLAUDE.md"
    if _has_zerosearch(candidate):
        result["project"] = True
        result["project_path"] = str(candidate)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="ZeroSearch 排他性搜索策略注册")
    parser.add_argument(
        "--scope",
        choices=["user", "project", "none"],
        default="none",
        help="注册位置 (默认: none 清除所有)",
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help="检测当前注册状态",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="项目根目录 (仅 --scope project 时使用)",
    )
    args = parser.parse_args()

    if args.detect:
        status = detect()
        for k, v in status.items():
            print(f"  {k}: {v}")
        return 0

    project_root = Path(args.project_root) if args.project_root else None
    ok = register(args.scope, project_root)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
