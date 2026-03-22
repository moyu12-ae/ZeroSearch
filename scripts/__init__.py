"""
Google AI Mode Skill for Trae
Browser automation layer using agent-browser CLI - Connect Mode Only

This skill only uses Connect Mode - agent-browser CLI connects to your real Chrome browser
via Chrome DevTools Protocol (CDP).

Key features:
- Zero token overhead (no browser state management)
- No CAPTCHA (uses your logged-in session)
- Full authentication reuse
- Low latency (direct CDP connection)
- No external HTML parsing dependencies (bs4-free)
- Built-in retry logic for reliability
- 3-layer AI Mode completion detection (SVG/aria-label/text)
- DOM injection citation extraction
- AI Mode availability detection
- Multi-language support (EN/DE/NL/ES/FR/IT)
- Persistent context with cookies storage
- HTTP Headers customization (Accept-Language)

Usage:
    from scripts import SearchEngine, RateLimiter, RateLimitConfig, RateLimitMode

    engine = SearchEngine(connect_port=9222)
    limiter = RateLimiter(config=RateLimitConfig.from_mode(RateLimitMode.BALANCED))

    result = engine.search("your query")

Version: 6.3.0
"""

from .browser import (
    BrowserManager,
    BrowserError,
    BrowserNotRunningError,
    CommandExecutionError,
    PageSnapshot,
    DEFAULT_PROFILE_DIR,
    DEFAULT_HEADERS,
)

from .search import (
    SearchEngine,
    SearchError,
    SearchResult,
    Citation,
    AIOverviewNotFoundError,
    AIModeNotAvailableError,
    CAPTCHAError,
)

from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitMode,
    create_rate_limiter,
)

from .fingerprint import (
    FingerprintGenerator,
)

from .captcha_handler import (
    AntiBotDetector,
    CaptchaResult,
)

from .cooling_manager import (
    CoolingManager,
    CoolingResult,
)

from .smart_timeout import (
    SmartTimeout,
    SmartTimeoutConfig,
    create_smart_timeout,
)

from .incremental_saver import (
    IncrementalSaver,
    SearchResultRecord,
)

from .smart_rate_limiter import (
    SmartRateLimiter,
    SmartRateLimiterConfig,
)

from .batch_search import (
    BatchSearchEngine,
    BatchSearchConfig,
    BatchSearchResult,
    create_batch_engine,
)

from .citation_cleaner import (
    CitationCleaner,
)

from .performance_monitor import (
    PerformanceMonitor,
    SearchMetric,
)

from .cache_manager import (
    UnifiedCacheManager,
    CacheConfig,
    create_cache,
)

__all__ = [
    # Browser
    "BrowserManager",
    "BrowserError",
    "BrowserNotRunningError",
    "CommandExecutionError",
    "PageSnapshot",

    # Search
    "SearchEngine",
    "SearchError",
    "SearchResult",
    "Citation",
    "AIOverviewNotFoundError",
    "AIModeNotAvailableError",
    "CAPTCHAError",

    # Rate Limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitMode",
    "create_rate_limiter",

    # Fingerprint
    "FingerprintGenerator",

    # CAPTCHA
    "AntiBotDetector",
    "CaptchaResult",

    # Cooling
    "CoolingManager",
    "CoolingResult",

    # Smart Timeout
    "SmartTimeout",
    "SmartTimeoutConfig",
    "create_smart_timeout",

    # Incremental Saver
    "IncrementalSaver",
    "SearchResultRecord",

    # Smart Rate Limiter
    "SmartRateLimiter",
    "SmartRateLimiterConfig",

    # Batch Search
    "BatchSearchEngine",
    "BatchSearchConfig",
    "BatchSearchResult",
    "create_batch_engine",

    # Citation Cleaner
    "CitationCleaner",

    # Performance Monitor
    "PerformanceMonitor",
    "SearchMetric",

    # Cache Manager
    "UnifiedCacheManager",
    "CacheConfig",
    "create_cache",

    # Constants
    "DEFAULT_PROFILE_DIR",
    "DEFAULT_HEADERS",
]

__version__ = "6.4.0"
