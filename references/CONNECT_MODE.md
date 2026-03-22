# Connect Mode Guide

## Overview

Connect Mode allows the skill to control your real Chrome browser via Chrome DevTools Protocol (CDP). This provides:

- ✅ **Low Token Consumption**: agent-browser's output is minimal
- ✅ **High Automation**: Uses your real Chrome with login session
- ✅ **No CAPTCHA**: Your logged-in session bypasses CAPTCHA
- ✅ **Fast**: No need to setup authentication state files

## Setup

### Step 1: Start Chrome with Debugging

macOS:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-debug-profile" &
```

Linux:
```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-debug-profile" &
```

Windows:
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%USERPROFILE%\chrome-debug-profile"
```

### Step 2: Login to Google (One-time)

1. Open Chrome to `http://localhost:9222`
2. Navigate to Google
3. Login with your Google account
4. Complete any verification required

### Step 3: Use Connect Mode

```python
from scripts import SearchEngine

engine = SearchEngine(connect_port=9222)
result = engine.search("your query")
print(result.markdown_output)
```

## Technical Details

### How It Works

1. agent-browser connects to Chrome via CDP
2. Batch commands execute JavaScript in the page context
3. Results are parsed as JSON for efficient extraction

### Advantages vs Other Methods

| Method | Token Cost | Automation | CAPTCHA | Setup |
|--------|-----------|------------|---------|-------|
| Default agent-browser | Low | High | Medium | Medium |
| State file | Low | High | Low | High |
| **Connect Mode** | **Low** | **High** | **None** | **Low** |
| patchright | High | High | Low | Medium |

### Troubleshooting

#### Connection Refused

Ensure Chrome is running with debugging port:
```bash
lsof -i :9222
```

#### Authentication Lost

Re-login to Google in the Chrome window

#### Port Already in Use

Use a different port (e.g., 9223)

## Security Notes

- The debugging port should not be exposed publicly
- Only use trusted networks
- Chrome profile data is stored locally
