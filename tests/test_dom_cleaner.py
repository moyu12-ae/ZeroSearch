"""Unit tests for DOM Cleaner (T3.1.3 / CH-03)"""
import sys
sys.path.insert(0, '.')
from src.extractor.dom_cleaner import clean_html


class TestDOMCleaner:
    def test_remove_script(self):
        html = '<html><body><script>alert(1)</script><p>Hello</p></body></html>'
        result = clean_html(html)
        assert 'script' not in result.lower()
        assert 'Hello' in result

    def test_remove_style(self):
        html = '<html><body><style>.x{color:red}</style><p>Hello</p></body></html>'
        result = clean_html(html)
        assert 'style' not in result.lower()
        assert 'Hello' in result

    def test_remove_nav_footer(self):
        html = '<nav>Menu</nav><p>Content</p><footer>Bottom</footer>'
        result = clean_html(html)
        assert 'Menu' not in result
        assert 'Bottom' not in result
        assert 'Content' in result

    def test_preserve_content(self):
        html = '<main><h1>Title</h1><p>Paragraph</p><ul><li>Item</li></ul></main>'
        result = clean_html(html)
        assert 'Title' in result
        assert 'Paragraph' in result
        assert 'Item' in result

    def test_empty_input(self):
        assert clean_html('') == ''

    def test_remove_attributes(self):
        html = '<p class="foo" style="bar" onclick="alert(1)" jsname="x">Hello</p>'
        result = clean_html(html)
        assert 'class=' not in result
        assert 'style=' not in result
        assert 'onclick' not in result
        assert 'jsname' not in result
        assert 'Hello' in result
