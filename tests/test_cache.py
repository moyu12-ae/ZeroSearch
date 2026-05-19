"""Unit tests for LRU Cache (T5.2.2 / CH-03)"""
import time
import sys
sys.path.insert(0, '.')
from src.search.cache import LRUCache


class TestLRUCache:
    def test_put_and_get(self):
        c = LRUCache(max_size=10, ttl_seconds=300)
        c.put('key1', {'data': 'value1'})
        result = c.get('key1')
        assert result is not None
        assert result['data'] == 'value1'

    def test_cache_miss(self):
        c = LRUCache(max_size=10, ttl_seconds=300)
        assert c.get('nonexistent') is None

    def test_normalized_key(self):
        c = LRUCache(max_size=10, ttl_seconds=300)
        c.put('React Hooks', {'data': 'test'})
        r1 = c.get('react hooks')
        r2 = c.get('REACT HOOKS')
        assert r1 is not None and r1['data'] == 'test'
        assert r2 is not None and r2['data'] == 'test'

    def test_lru_eviction(self):
        c = LRUCache(max_size=3, ttl_seconds=300)
        for i in range(5):
            c.put(f'key_{i}', {'data': i})
        assert len(c) == 3, f"Expected 3, got {len(c)}"
        assert c.get('key_0') is None  # should be evicted
        assert c.get('key_1') is None  # should be evicted

    def test_ttl_expiry(self):
        c = LRUCache(max_size=10, ttl_seconds=0.001)
        c.put('key1', {'data': 'value1'})
        time.sleep(0.01)
        assert c.get('key1') is None  # TTL expired after 10ms

    def test_stats(self):
        c = LRUCache(max_size=10, ttl_seconds=300)
        c.put('k1', {'data': 1})
        c.get('k1')  # hit
        c.get('k2')  # miss
        s = c.stats()
        assert s['hits'] >= 1
        assert s['misses'] >= 1

    def test_clear(self):
        c = LRUCache(max_size=10, ttl_seconds=300)
        c.put('k1', {'data': 1})
        c.put('k2', {'data': 2})
        c.clear()
        assert len(c) == 0
        assert c.get('k1') is None
