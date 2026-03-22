# Troubleshooting Guide

## Common Issues and Solutions

### 1. ModuleNotFoundError

**Problem**: `ModuleNotFoundError: No module named 'scripts'`

**Solution**: Run `./setup.sh` to install dependencies, or ensure you're running from the correct directory.

```bash
cd /path/to/ZeroSearch
./setup.sh
```

### 2. CAPTCHA Required

**Problem**: Every search triggers CAPTCHA

**Solution**: Use Connect Mode with your real Chrome browser:

```python
from scripts import SearchEngine

engine = SearchEngine(connect_port=9222)
result = engine.search("your query")
```

Setup process:
1. Start Chrome with debugging port:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-debug-profile" &
```

2. Login to Google in the Chrome window (one-time)

### 3. AI Mode Not Available

**Problem**: AI Mode is not available in your region

**Solution**: Use a VPN from US/UK/DE, or change browser language settings.

### 4. Browser Fails to Start

**Problem**: agent-browser fails to launch

**Solution**:
1. Verify internet connection
2. Verify Chrome installation
3. Run in headed mode to debug:
```python
engine = SearchEngine(headless=False)
```

### 5. No Citations Found

**Problem**: AI Overview appears but no citations extracted

**Solution**:
1. Increase wait time:
```python
engine = SearchEngine(wait_time=5)
```

2. Use Connect Mode with JavaScript extraction:
```python
engine = SearchEngine(connect_port=9222)
```

### 6. Profile Corrupted

**Problem**: Browser profile is corrupted

**Solution**: Reset profile:
```python
from scripts import ProfileManager
pm = ProfileManager()
pm.reset()
```

### 7. Port Already in Use

**Problem**: CDP port 9222 is already in use

**Solution**: Use a different port:
```python
engine = SearchEngine(connect_port=9223)
```
