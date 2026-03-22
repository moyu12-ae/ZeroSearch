---
name: ZeroSearch
description: "**Zero-cost web search with real Chrome.** Search the web using Google with source citations. **ONLY uses Connect Mode with real Chrome** - connects to your existing browser via CDP for zero token overhead, no CAPTCHA, and full login session reuse. Use this skill whenever the user asks for current information, library docs, coding examples, technical comparisons, or needs web research with traceable sources. Returns summaries with inline Markdown links. Essential for queries about recent technologies, post-2025 events, library/framework documentation. Make sure to use this skill when the user mentions \"search\", \"find latest\", \"current docs\", \"web research\", or asks \"what's new in [technology]\" after 2025.
compatibility:
  - Trae IDE
  - Claude Code
  - Claude.ai"
---

# ZeroSearch - Zero-Cost Web Search for Trae

Query Google to retrieve comprehensive, source-grounded answers with inline citations.

## Architecture

This skill **ONLY uses Connect Mode** - agent-browser CLI connects to your real Chrome browser via Chrome DevTools Protocol (CDP).

```
User Query → SearchEngine → agent-browser batch --json → Real Chrome (CDP:9222) → Summary + Citations
```

**Why Connect Mode Only:**
- ✅ Zero token overhead (no browser state management)
- ✅ No CAPTCHA (uses your logged-in session)
- ✅ Full authentication reuse
- ✅ Low latency (direct CDP connection)
- ✅ No browser data sync needed
- ✅ Built-in retry logic for reliability
- ✅ bs4-free (uses native agent-browser commands)
- ✅ 3-layer AI Mode detection (SVG/aria-label/text)
- ✅ DOM injection citation extraction
- ✅ AI Mode availability detection
- ✅ Multi-language support (EN/DE/NL/ES/FR/IT)
- ✅ Persistent context with cookies storage
- ✅ HTTP Headers customization (Accept-Language: en-US)

## Prerequisites

### 1. Install agent-browser CLI

```bash
npm install -g agent-browser
agent-browser install
```

### 2. Start Chrome with Debugging Port

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-debug-profile" &

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-debug-profile" &

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%USERPROFILE%\chrome-debug-profile"
```

### 3. Login to Google (One-time)

1. Open Chrome to `http://localhost:9222`
2. Navigate to Google and login
3. Complete any verification

## Usage

### Basic Search

```python
from scripts import SearchEngine

engine = SearchEngine(connect_port=9222)
result = engine.search("your query")
print(result.markdown_output)
```

### Python API

```python
from scripts import SearchEngine, Citation

engine = SearchEngine(
    connect_port=9222,
    max_retries=3     # Retry attempts for transient failures
)

result = engine.search("React best practices 2026")

# Access results
print(result.summary)           # Page summary text
print(result.markdown_output)  # Formatted Markdown
print(result.ai_mode_available)  # True if AI Mode is available

for citation in result.citations:
    print(f"[{citation.title}]({citation.url})")
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `connect_port` | 9222 | CDP port for real Chrome |
| `max_retries` | 3 | Retry attempts for transient failures |
| `profile_dir` | ~/.cache/zero-search/chrome_profile | Directory for cookies storage |
| `headers` | {"Accept-Language": "en-US,en;q=0.9"} | HTTP headers for requests |

## Output Format

Returns Markdown with citations:

```markdown
## Your Search Query

Summary text from the page.

**Sources:**

- [Source Title](https://example.com)
- [Another Source](https://example.org)
```

## Features

### 3-Layer AI Mode Completion Detection

The skill uses a **3-layer detection system** (adapted from the original Playwright implementation):

1. **Layer 1: SVG thumbs-up icon** (most reliable, language-independent)
   - Detects `button svg[viewBox="3 3 18 18"]`
   - This is the gold standard for AI Mode completion

2. **Layer 2: aria-label buttons**
   - Detects buttons with aria-label containing "feedback", "related", or "source"
   - Language-independent

3. **Layer 3: Text polling** (multi-language)
   - Polls for text indicators in multiple languages:
   - English: `AI-generated`, `AI Overview`, `Generative AI is experimental`
   - German: `KI-generiert`, `KI-Antworten`
   - Dutch: `AI-gegenereerd`
   - Spanish: `Las respuestas de la IA`
   - French: `Les réponses de l'IA`
   - Italian: `Risposte IA`

### DOM Injection Citation Extraction

The skill uses **DOM injection** to extract citations:

1. Finds AI Overview container (`[data-container-id="main-col"]`)
2. Clicks citation buttons (`[aria-label="View related links"]`)
3. Extracts links from sidebar (`[data-container-id="rhs-col"]`)
4. Filters out Google internal domains
5. Smart title extraction (see below)

### Smart Title Extraction

The skill uses a **4-layer title extraction** to avoid "Link N" titles:

1. **aria-label attribute** - Often has the site name for Google results
2. **title attribute** - Link's title attribute
3. **textContent** - Full text inside the element
4. **Parent element text** - Text from parent container

This ensures meaningful titles even when Google search result links have empty textContent.

### AI Mode Availability Detection

The skill automatically detects if AI Mode is unavailable in your region:

- Detects text like "AI Mode is not available in your country or language"
- Returns a clear error message with suggestions
- Suggests using a VPN to access from a supported region

### Built-in Reliability
- **Automatic retry** with exponential backoff (3 retries by default)
- **Network idle detection** using `wait --load networkidle`
- **Graceful fallback** to fixed wait time if network detection fails
- **40-second timeout** for AI Mode completion detection

### bs4-free Design
- No external HTML parsing dependencies
- Uses native Python `html.parser` for HTML cleaning
- Simpler dependency management

### Multi-Language Support

Automatically detects and supports:
- English, German (Deutsch), Dutch, Spanish, French, Italian

### Persistent Context (Cookies Storage)

The skill saves cookies to a profile directory for session persistence:

- **Profile Directory**: `~/.cache/zero-search/chrome_profile`
- **Cookies File**: `cookies.json`
- **Local State**: `Local State` (for locale settings)

This helps:
- Reduce CAPTCHA occurrences across sessions
- Maintain login state between searches
- Preserve session authentication

### HTTP Headers Customization

The skill automatically sets HTTP headers to request English content:

```python
headers = {
    "Accept-Language": "en-US,en;q=0.9"
}
```

This helps ensure AI Mode is available and returns English results.

### Query Optimization

For best results, include:
- **Year (2026)** for current information
- **Specific aspects** in parentheses
- **Output format** request

**Example:**
```python
result = engine.search(
    "Rust async programming 2026 (tokio, async/await, best practices). Code examples."
)
```

## Troubleshooting

### Chrome Not Found on Port 9222

```bash
# Check if Chrome is running with debugging
lsof -i :9222
```

### Connection Refused

1. Restart Chrome with debugging port
2. Ensure no firewall blocking
3. Check port number matches

### No Citations Found

- AI Mode may not be available in your region (check `result.ai_mode_available`)
- Try using a VPN to access from US, UK, Germany, etc.
- The skill will still extract citations from regular search results as fallback

### AI Mode Not Available

If you see "AI Mode is not available in your country or language":

1. **Use a VPN** to connect from a supported region (US, UK, Germany, etc.)
2. **Check your Chrome locale** - ensure it's set to a supported language
3. The skill will fall back to extracting citations from standard search

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Chrome not running with CDP | Restart Chrome with `--remote-debugging-port=9222` |
| Empty results | Page not loaded | Check network or increase wait time |
| Transient failure | Network issue | Automatic retry (3 attempts) |
| AI Mode not available | Region restriction | Use VPN to access from supported region |

## Security Notes

- Debugging port should not be exposed publicly
- Only use trusted networks
- Your login session is used directly