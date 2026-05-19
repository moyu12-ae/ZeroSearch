"""Unit tests for Footnote Formatter (T4.1.2 / CH-03)"""
import sys
sys.path.insert(0, '.')
from src.converter.footnote_formatter import Citation, format_footnotes


class TestFootnotes:
    def test_basic_footnote(self):
        text = 'React is a JavaScript library for building UIs.'
        citations = [Citation(title='React Docs', url='https://react.dev', index=1)]
        result = format_footnotes(text, citations)
        assert '[1]' in result
        assert '## Sources' in result
        assert 'React Docs' in result
        assert 'https://react.dev' in result

    def test_multiple_footnotes(self):
        text = 'React is popular.\n\nVue is also good.'
        citations = [
            Citation(title='React', url='https://react.dev', index=1),
            Citation(title='Vue', url='https://vuejs.org', index=2),
        ]
        result = format_footnotes(text, citations)
        assert '[1]' in result
        assert '[2]' in result

    def test_no_citations(self):
        text = 'Just some text without any citations.'
        result = format_footnotes(text, [])
        assert '## Sources' not in result
        assert '---' not in result
        assert text in result

    def test_empty_text(self):
        result = format_footnotes('', [
            Citation(title='Test', url='https://example.com', index=1)
        ])
        assert '[1]' in result
