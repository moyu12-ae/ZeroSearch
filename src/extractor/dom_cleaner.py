"""
DOM 清洗模块 (T3.1.3)
用 BeautifulSoup4 移除 HTML 中无关标签和属性，保留有意义内容。
"""

from __future__ import annotations

import re
from typing import List

from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# 清洗规则常量
# 来源: .anws/v1/04_SYSTEM_DESIGN/content-extractor.md §6.4
# ---------------------------------------------------------------------------

REMOVE_TAGS: List[str] = [
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "noscript",
    "iframe",
    "svg",
    "form",
    "input",
    "button",
    "img",   # AI 原生优化: 去除图片 (token 消耗大)
]

REMOVE_ATTRIBUTES_PATTERNS: List[str] = [
    "class",
    "style",
    "id",
    r"^data-",           # 所有 data-* 属性
    "jsname",
    "jsaction",
    "jscontroller",
    "onclick",
    "onload",
    r"^aria-",           # ARIA 无障碍标记
]

REMOVE_SELECTORS: List[str] = [
    '[role="navigation"]',
    '[role="banner"]',
    '[role="contentinfo"]',
    '[aria-label*="advertisement"]',
    ".ad-container",
    ".google-ad",
    "#taw",
    "#top_nav",
    "#fbar",
    "#bfoot",
]

# Extra attribute that the acceptance criteria explicitly call out for removal
# beyond the pattern-based ones above (data-ved, jsname, jsaction are already
# covered by ^data- and the explicit entries).
EXTRA_ATTRIBUTES: List[str] = [
    "data-ved",
    "jsaction",
    "onload",
    "jsname",
    "jscontroller",
    "onclick",
    "style",
    "class",
    "id",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _should_remove_attribute(attr_name: str) -> bool:
    """Return True if *attr_name* matches any REMOVE_ATTRIBUTES_PATTERNS."""
    for pattern in REMOVE_ATTRIBUTES_PATTERNS:
        if pattern.startswith("^"):
            if re.match(pattern, attr_name):
                return True
        else:
            if attr_name == pattern:
                return True
    return False


def _clean_attributes(tag: Tag) -> None:
    """Strip unwanted attributes from a BeautifulSoup Tag in-place."""
    attrs_to_remove = [a for a in tag.attrs if _should_remove_attribute(a)]
    for attr in attrs_to_remove:
        del tag[attr]


def _remove_by_selectors(soup: BeautifulSoup) -> None:
    """Remove elements matching CSS selectors in REMOVE_SELECTORS."""
    for sel in REMOVE_SELECTORS:
        for element in soup.select(sel):
            element.decompose()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clean_html(raw_html: str) -> str:
    """Clean incoming HTML by removing non-content tags and attributes.

    Parameters
    ----------
    raw_html : str
        Raw HTML string to clean.

    Returns
    -------
    str
        Cleaned HTML string.  Returns an empty string when the input is
        empty or whitespace-only.

    Raises
    ------
    ValueError
        When *raw_html* is empty or whitespace-only.
    """
    # Edge-case: empty input
    if not raw_html or not raw_html.strip():
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remove elements matched by CSS selectors (ads, nav roles, etc.)
    _remove_by_selectors(soup)

    # 2. Decompose tags listed in REMOVE_TAGS (script, style, nav, footer, …)
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 3. Strip unwanted attributes from remaining tags
    for tag in soup.find_all(True):
        _clean_attributes(tag)

    # Return the string representation of the cleaned body content.
    # When <body> exists we return its inner HTML; otherwise return the soup
    # as a string.
    body = soup.body
    result = ""
    if body is not None:
        result = "".join(str(child) for child in body.contents)
    else:
        result = str(soup)

    # AI 原生优化: 清除 Google AI Mode 特有的 UI 噪音
    result = _strip_google_ui_noise(result)
    return result


# Google AI Mode UI 噪音文本（AI 消费端不需要）
_UI_NOISE_PATTERNS = [
    r"Skip to main content",
    r"Accessibility help",
    r"Accessibility feedback",
    r"Quick Settings",
    r"AI Mode history",
    r"New thread",
    r"You're signed out",
    r"To access history and more,",
    r"sign in to your account",
    r"Delete all searches\?",
    r"You won't be able to return to these responses",
    r"Delete all",
    r"Manage public links",
    r"My Google Search History",
    r"AI can make mistakes,? so double-check responses",
    r"Copy\n",
    r"Share public link",
    r"This public link is valid for 7 days",
    r"Creating a public link\.\.\.",
    r"Facebook\n",
    r"Gmail\n",
    r"X\n",
    r"Reddit\n",
    r"WhatsApp\n",
    r"Good response\n",
    r"Bad response\n",
    r"Saved time\n",
    r"Clear\n",
    r"Helpful\n",
    r"Comprehensive\n",
    r"Other\n",
    r"Incorrect\n",
    r"Inappropriate\n",
    r"Not working\n",
    r"Unhelpful\n",
    r"A copy of this chat will be included",
    r"Your feedback will include a copy",
    r"Set browser language",
    # 多语言 UI 噪音 (中文繁/简 + 日文)
    r"跳至主內容",
    r"無障礙功能說明",
    r"无障碍功能说明",
    r"快速設定",
    r"快速设置",
    r"AI 模式記錄",
    r"AI 模式记录",
    r"新增討論串",
    r"新增讨论串",
    r"你已登出帳戶",
    r"你已登出账户",
    r"要刪除所有搜尋記錄嗎",
    r"要删除所有搜索记录吗",
    r"全部刪除",
    r"全部删除",
    r"管理公開連結",
    r"管理公开链接",
    r"我的 Google 搜尋記錄",
    r"我的 Google 搜索记录",
    r"AI 可能會出錯，?請查證回覆內容",
    r"AI 可能会出错，?请查证回复内容",
    r"複製\n",
    r"复制\n",
    r"分享公開連結",
    r"分享公开链接",
    r"這個公開連結會在 7 天後失效",
    r"良好的回應\n",
    r"良好的回应\n",
    r"有待加強\n",
    r"有待加强\n",
    r"省時\n",
    r"省时\n",
    r"有幫助\n",
    r"有帮助\n",
    r"不正確\n",
    r"不正确\n",
    r"不當的\n",
    r"不当的\n",
    r"無法運作\n",
    r"无法运作\n",
    r"沒有幫助\n",
    r"没有帮助\n",
    r"我的廣告中心",
    r"我的广告中心",
    r"語言設定",
    r"语言设置",
    r"感謝你通知我們",
    r"感谢你通知我们",
    r"意見回饋",
    r"意见反馈",
    r"這段對話副本會附加到你的意見回饋",
    r"这段对话副本会附加到你的意见反馈",
    r"意見回饋內容將包含這段對話",
    r"意见反馈内容将包含这段对话",
    r"你的意見回饋會附上這段對話的副本",
    r"你的意见反馈会附上这段对话的副本",
    r"Google 可能會根據",
    r"Google 可能会根据",
    r"提出依法移除要求",
    r"搜尋結果",
    r"搜索结果",
    r"Google 應用程式",
    r"Google 应用",
    r"顯示全部",
    r"显示全部",
    r"undefined\n",
    r"關閉\n",
    r"关闭\n",
    r"更多輸入選項",
    r"更多输入选项",
    r"麥克風",
    r"麦克风",
    r"停止\n",
    r"傳送\n",
    r"传送\n",
    r"詢問相關資訊",
    r"询问相关信息",
    r"Looking for results in English\?",
    r"Change to English",
    r"繼續使用 .+中文",
    r"继续使用 .+中文",
    r"AI 模式回應已就緒",
    r"AI 模式回应已就绪",
    r"圖片\n",
    r"图片\n",
    r"影片\n",
    r"视频\n",
    r"新聞\n",
    r"新闻\n",
    r"購物\n",
    r"购物\n",
    r"地圖\n",
    r"地图\n",
    r"書籍\n",
    r"书籍\n",
    r"航班\n",
    r"財經\n",
    r"财经\n",
    r"Google 可能會根據《?隱私權政策》?",
    r"隐私权政策",
    r"服務條款",
    r"服务条款",
    r"提出依法移除要求",
    # 日文 UI 噪音
    r"メインコンテンツにスキップ",
    r"アクセシビリティヘルプ",
    r"クイック設定",
    r"AIモード履歴",
    r"新しいスレッド",
    r"ログアウトしています",
    r"すべて削除",
    r"公開リンクを管理",
    r"検索結果",
    r"すべて表示",
    r"閉じる",
]


def _strip_google_ui_noise(html: str) -> str:
    """移除 Google AI Mode 页面特有的 UI 噪音文本。

    这些文本在 AI 消费端毫无价值，纯粹浪费 token。
    """
    for pattern in _UI_NOISE_PATTERNS:
        html = re.sub(pattern, '', html)
    # 去除连续空行 (>2)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()
