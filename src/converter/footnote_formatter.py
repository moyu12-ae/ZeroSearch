"""脚注格式化模块 — 脚注插入 + Sources 段落生成。

职责:
  - 在 AI 文本段落末尾插入内联脚注标记 [1][2]
  - 在文档末尾生成 ## Sources: 段落
  - 无引用时省略 Sources 段落

设计依据: markdown-converter.md 8.1 — 段落末尾策略 (选项 A)
"""

from dataclasses import dataclass
import re


@dataclass
class Citation:
    """引用数据，表示一条来源信息。"""
    title: str
    url: str
    index: int = 0


def format_footnotes(ai_text: str, citations: list) -> str:
    """在段落末尾插入脚注 [1][2]，末尾追加 ## Sources 段落。

    算法:
      1. citations 列表顺序即为 AI 文本中出现顺序
      2. 遍历每个段落，检查段落内是否出现引用 URL 或域名
      3. 匹配到的引用在段落末尾追加脚注标记 [N]
      4. 同一 URL 仅在首次出现段落插入脚注
      5. 文档末尾追加 ## Sources: 段落

    Args:
        ai_text: AI 回答正文（已转换为 Markdown）
        citations: Citation 列表，按引用出现顺序排列

    Returns:
        完整的 Markdown 字符串（正文 + 脚注 + Sources）
    """
    if not citations:
        return ai_text

    # 分配 citation index（1-based），按列表顺序分配
    indexed_citations = _assign_indices(citations)

    # 按段落拆分（以 \n\n 为边界）
    paragraphs = _split_paragraphs(ai_text)

    # 记录已有脚注的段落（段落索引 -> [脚注索引列表]）
    paragraph_footnote_map = _match_citations_to_paragraphs(
        paragraphs, indexed_citations
    )

    # 在段落末尾插入脚注
    text_with_footnotes = _insert_footnote_markers(paragraphs, paragraph_footnote_map)

    # 构建 Sources 段落
    text_with_footnotes = text_with_footnotes.rstrip()
    text_with_footnotes += '\n\n---\n\n## Sources:\n\n'
    text_with_footnotes += _build_sources_section(indexed_citations)

    return text_with_footnotes


def _assign_indices(citations: list) -> list:
    """按列表顺序为 Citation 分配 1-based index。

    若调用方已预设 index（index > 0），则保留；否则按顺序分配。
    """
    result = []
    next_index = 1
    for cit in citations:
        if cit.index <= 0:
            result.append(Citation(title=cit.title, url=cit.url, index=next_index))
            next_index += 1
        else:
            result.append(cit)
            if cit.index >= next_index:
                next_index = cit.index + 1
    return result


def _split_paragraphs(text: str) -> list:
    """按双换行拆分段落，返回纯段落文本列表。"""
    if not text:
        return []
    return text.split('\n\n')


def _match_citations_to_paragraphs(
    paragraphs: list,
    indexed_citations: list,
) -> dict:
    """匹配引用到段落，每个段落记录应插入的脚注索引列表。

    匹配策略（按优先级降序）:
      1. 完整 URL 出现在段落中
      2. 去掉协议后的 URL 出现在段落中
      3. 域名出现在段落中
      4. 标题关键词匹配（作为兜底）

    Args:
        paragraphs: 段落文本列表
        indexed_citations: 已分配 index 的 Citation 列表

    Returns:
        {paragraph_index: [footnote_index, ...]}
    """
    paragraph_footnotes = {}
    used_indices = set()

    for cit in indexed_citations:
        url = cit.url
        idx = cit.index
        title = cit.title

        if idx in used_indices:
            continue

        matched = False
        for pi, para in enumerate(paragraphs):
            if _citation_matches_paragraph(url, title, para):
                if pi not in paragraph_footnotes:
                    paragraph_footnotes[pi] = []
                paragraph_footnotes[pi].append(idx)
                used_indices.add(idx)
                matched = True
                break

        if not matched:
            # 没有匹配到任何段落，追加到最后一个段落
            if paragraphs:
                last_pi = len(paragraphs) - 1
                if last_pi not in paragraph_footnotes:
                    paragraph_footnotes[last_pi] = []
                paragraph_footnotes[last_pi].append(idx)
                used_indices.add(idx)

    return paragraph_footnotes


def _citation_matches_paragraph(url: str, title: str, paragraph: str) -> bool:
    """判断引用是否与段落内容相关。

    匹配策略（按优先级降序）:
      1. 完整 URL 出现在段落中
      2. 去掉协议后的 URL 出现在段落中
      3. 域名出现在段落中
      4. 标题关键词出现在段落中（兜底）
    """
    if not url or not paragraph:
        return False

    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        # 策略1: 完整 URL
        if url in paragraph:
            return True

        # 策略2: 去掉协议后的 URL
        for scheme_removed in _url_variants(url):
            if scheme_removed in paragraph:
                return True

        # 策略3: 域名匹配
        if parsed.netloc and parsed.netloc in paragraph:
            return True

        # 策略4: 标题关键词匹配（取标题中较长的词，避免误匹配）
        if title:
            key_tokens = _extract_key_tokens(title)
            for token in key_tokens:
                if token.lower() in paragraph.lower():
                    return True
    except Exception:
        pass

    return False


def _url_variants(url: str) -> list:
    """生成不带协议前缀的 URL 变体。"""
    variants = []
    if '://' in url:
        variants.append(url.split('://', 1)[1])
        # 去掉 www 前缀
        no_www = url.split('://', 1)[1]
        if no_www.startswith('www.'):
            variants.append(no_www[4:])
    else:
        variants.append(url)
    return variants


def _extract_key_tokens(title: str) -> list:
    """从标题中提取可用于匹配的关键词。

    优先取纯字母的、长度>=3的词，按长度降序排列。
    """
    words = re.findall(r'[a-zA-Z]{3,}', title)
    # 按长度降序，长词优先（减少误匹配）
    words.sort(key=len, reverse=True)
    return words


def _insert_footnote_markers(
    paragraphs: list,
    footnote_map: dict,
) -> str:
    """将脚注标记 [1][2] 插入到对应段落的末尾。

    Args:
        paragraphs: 原始段落列表
        footnote_map: {段落索引: [脚注索引列表]}

    Returns:
        拼接后的完整文本
    """
    if not paragraphs:
        return ''

    result_parts = []
    for pi, para in enumerate(paragraphs):
        part = para
        if pi in footnote_map and footnote_map[pi]:
            indices = sorted(footnote_map[pi])
            marks = ''.join(f'[{i}]' for i in indices)
            part = part.rstrip() + ' ' + marks
        result_parts.append(part)

    return '\n\n'.join(result_parts)


def _build_sources_section(citations: list) -> str:
    """构建 ## Sources: 段落内容。

    格式: [N] **{title}**  \n{url}\n
    （两个空格用于 Markdown 强制换行）
    """
    lines = []
    for cit in citations:
        lines.append(f'[{cit.index}] **{cit.title}**  \n{cit.url}\n')
    return '\n'.join(lines)
