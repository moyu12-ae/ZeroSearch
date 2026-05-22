"""文件保存策略 (File Save Strategy)

负责将 Markdown 搜索结果保存为时间戳命名的文件。
命名规则: results/YYYY-MM-DD_HH-MM-SS_Query_Name.md
"""

import os
import re
from datetime import datetime


def _sanitize_filename(name: str, max_length: int = 50) -> str:
    """清理文件名，替换非法字符为下划线。

    规则:
      - 替换空格为下划线
      - 移除非法文件名字符: / \\ : * ? " < > |
      - 截断至 max_length 字符
      - 移除前后空白
    """
    # 替换空格为下划线
    sanitized = name.replace(" ", "_")
    # 移除 Windows / Unix 非法文件名字符
    sanitized = re.sub(r'[/\\:*?"<>|]', "_", sanitized)
    # 合并连续下划线
    sanitized = re.sub(r"_+", "_", sanitized)
    # 去除前后下划线
    sanitized = sanitized.strip("_")
    # 截断
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("_")
    return sanitized


def _generate_filename(query: str) -> str:
    """生成时间戳文件名。

    格式: YYYY-MM-DD_HH-MM-SS_Query_Name.md

    Args:
        query: 搜索查询字符串

    Returns:
        不含目录路径的文件名
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    query_part = _sanitize_filename(query) if query else "untitled"
    if not query_part:
        query_part = "untitled"
    return f"{timestamp}_{query_part}.md"


def save_result(markdown: str, query: str, output_dir: str = "results") -> str:
    """保存搜索结果到文件，返回文件路径。

    - 时间戳命名: YYYY-MM-DD_HH-MM-SS_Query_Name.md
    - 文件名非法字符替换为 _
    - 目录不存在时自动创建
    - 幂等: 同一时间戳+查询名覆盖写入
    - 相对路径自动解析为项目根目录下的子目录

    Args:
        markdown: Markdown 文本内容
        query: 搜索查询字符串
        output_dir: 输出目录，默认为 "results" (相对路径解析为项目根下)

    Returns:
        写入文件的绝对路径
    """
    # 相对路径解析为项目根目录下的子目录
    if not os.path.isabs(output_dir):
        project_root = Path(__file__).resolve().parent.parent.parent
        output_dir = str(project_root / output_dir)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名并拼接完整路径
    filename = _generate_filename(query)
    filepath = os.path.join(output_dir, filename)

    # 写入文件（覆盖模式，保证幂等）
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    return os.path.abspath(filepath)
