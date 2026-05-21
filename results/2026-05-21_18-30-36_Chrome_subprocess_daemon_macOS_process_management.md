[](https://support.google.com/websearch/answer/181196?hl=zh-HK) [10][13]

無障礙功能意見

---


如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm](https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm)

Chrome subprocess daemon macOS process management browser automation patterns

Direct Answer 

Manage Chrome subprocesses on macOS by combining native system tools (`launchd`, `kill`) with robust browser automation frameworks like Playwright or Puppeteer to prevent orphaned daemon processes. 

Chrome Architecture on macOS 

Google Chrome operates on a multi-process architecture. On macOS, this splits into several distinct processes visible in Activity Monitor: 

- **Browser Process:** The main coordinator managing the UI and orchestration.
- **Renderer Process:** Handles HTML, CSS, and JavaScript rendering (sandboxed).
- **GPU Process:** Manages graphics rendering tasks.
- **Helper Processes:** Labeled as `Google Chrome Helper`, these manage plug-ins, extensions, and network tasks. 


Native Process Management 

You can monitor and manage these daemons natively through the macOS Terminal. 

Identification 

Locate running Chrome processes and helpers: 

bash

```
# Find all Google Chrome related processes
ps aux | grep -i "Google Chrome"

```

請謹慎使用程式碼。

Force Termination 

If automated scripts crash, orphaned helpers may drain memory. Clear them instantly: 

bash

```
# Kill all Chrome Helper processes safely
pkill -f "Google Chrome Helper"

# Force kill all Chrome instances
killall "Google Chrome"

```

請謹慎使用程式碼。

Automation Patterns & Daemon Control 

Uncontrolled browser automation often leaves behind "zombie" processes. Use these implementation patterns to ensure clean execution. 

1. Playwright (Python) — Explicit Lifetime 

Playwright naturally handles process management via context managers, ensuring the daemon terminates even if exceptions occur. 

python

```
from playwright.sync_api import sync_playwright

def run_automation():
    # Use context manager to guarantee process cleanup
    with sync_playwright() as p:
        # headless=True prevents UI daemon overhead
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com")
  
        # Explicitly close before exiting context
        browser.close()

if __name__ == "__main__":
    run_automation()

```

請謹慎使用程式碼。

2. Puppeteer (Node.js) — Signal Handling 

Node.js processes require explicit event listeners to catch termination signals (like `SIGINT` or `SIGTERM`) and clean up the Chrome subprocess. 

javascript

```
const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        // Removes default arguments that might conflict with macOS sandbox
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.goto('https://example.com');

    // Handle unexpected script terminations gracefully
    const cleanup = async () => {
        await browser.close();
        process.exit();
    };

    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);

    await browser.close();
})();

```

請謹慎使用程式碼。

macOS Persistence via launchd 

To run a Chrome automation script as a continuous system daemon on macOS, utilize `launchd` by creating a property list (`.plist`) file in `~/Library/LaunchAgents/`. 

xml

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.chrome.automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>/Users/username/scripts/automation.js</string>
    </array>
    <key>KeepAlive</key>
    <false/>
    <key>StartInterval</key>
    <integer>3600</integer> <!-- Runs every hour -->
</dict>
</plist>

```

請謹慎使用程式碼。

Load the agent with: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.chrome.automation.plist` 

Troubleshooting Resource Leaks 

- **Disable Extensions:** Pass `--disable-extensions` in automation arguments to reduce helper process count.
- **Profile Directory Cleanup:** Use distinct `--user-data-dir` paths for automation, and clear them post-run to prevent disk bloat.
- **Zombie Hunting:** Implement a wrapper shell script that checks for orphaned `Google Chrome Helper` processes lacking a parent `Google Chrome` process id, then kills them. 


To help refine these patterns, tell me: 

- Which **programming language** or **automation framework** (Playwright, Selenium, Puppeteer) are you actively using?
- Are you experiencing a specific issue, like **memory leaks**, **zombie processes**, or **permission crashes** on macOS?
- Do you need this script to run **silently in the background** or on a **fixed schedule**? 


複製

，而且分享討論串，包括你新增的個人資訊。這個連結或其他人建立的副本無法刪除。如果分享到第三方服務，就適用於該方的政策。

正在建立公開連結...

Facebook

Gmail

X

Reddit

WhatsApp

良好的回應

有待加強

省時

清除

有幫助

全面

其他

不正確

不當的

無法運作

沒有幫助

其他

這段對話副本會附加到你的

內容將包含這段對話及你搜尋的圖片

你的會附上這段對話的副本、你分享的連結，以及搜尋的圖片。

《[隱私權政策](https://policies.google.com/privacy)》和《[https://policies.google.com/terms](https://policies.google.com/terms)》使用帳戶與系統資料，瞭解您的意見及提升服務品質。如有法律問題，請[https://support.google.com/legal/answer/3110420](https://support.google.com/legal/answer/3110420)。 [11][12]

- [](https://github.com/microsoft/playwright-cli/issues/388)
  
  
  
  Orphaned --browser chrome processes block normal Chrome on macOS · Issue #388 · microsoft/playwright-cli2026年4月29日 — When a daemon using --browser chrome ( channel: "chrome" ) dies ungracefully, the Chrome process it spawned becomes orphaned (PPID...
  
  
  GitHub
  

- [](https://www.mdsec.co.uk/2021/01/breaking-the-browser-a-tale-of-ipc-credentials-and-backdoors/)
  
  
  
  Breaking The Browser - A tale of IPC, credentials and backdoors2021年1月12日 — Like most browsers Chrome ( Google Chrome ) uses a multi-process architecture (as can be seen below):
  
  
  MDSec
  

- [](https://kashsecurity.medium.com/the-architecture-of-google-chrome-e943c20929f0)
  
  
  
  The Architecture of Google Chrome | by KAsh Security | Medium2025年8月16日 — * **Browser process** (a.k.a. the “chrome” of Chrome ( Google Chrome ) ): owns privileged capabilities and global coordination — U...
  
  
  Medium
  

- [](https://cabulous.medium.com/how-browser-works-part-i-process-and-thread-f63a9111bae9)
  
  
  
  How web browser works step by step [Latest]— high-level architecture (part 1) | by Carson | Medium2019年11月10日 — Fight against the instability Modern browsers put renderer and plugin processes separate from the browser process. The renderer pr...
  
  
  Medium
  

- [](https://medium.com/@YodgorbekKomilo/google-chrome-system-design-a-full-guide-1f6cd5bb6e8d)
  
  
  
  🧠 Google Chrome System Design — A Full Guide 🚀 | by Yodgorbek Komilov2025年6月22日 — 2. Renderer Process One per tab (typically). Executes: HTML/CSS parsing DOM construction JavaScript via the V8 engine Rendering an...
  
  
  Medium
  

- [](https://chromium.googlesource.com/playground/chromium-org-site/+/refs/heads/main/developers/design-documents/multi-process-architecture/index.md)
  
  
  
  Chromium - Multi-process ArchitectureWe refer to the main process that runs the UI and manages tab and plugin processes as the “browser process” or “browser.” Likewise...
  
  
  Google Open Source
  

- [](https://chromium.googlesource.com/playground/chromium-org-site/+/refs/heads/main/developers/design-documents/process-models.md)
  
  
  
  Chromium - Process ModelsSandboxes and plug-ins In each of the multi-process architectures, Chromium's renderer processes are executed within a sandboxed p...
  
  
  Google Open Source
  

- [](https://macsecurity.net/view/638-google-chrome-helper-renderer-high-cpu-mac)
  
  
  
  How to fix Google Chrome Helper (Renderer) high CPU Mac process issue2025年3月9日 — In the Activity Monitor app, look for Google Chrome Helper, Google Chrome Helper (Renderer), Google Chrome Helper (Plugin), Google...
  
  
  macsecurity.net
  

- [](https://www.browsercat.com/post/browser-automation-api-guide-for-developers)
  
  
  
  Browser Automation API Guide: Perfect Tools for Developers2025年2月20日 — But if you need to automate other browsers (Safari, Firefox) or prefer a different programming language, Puppeteer might scratch i...
  
  
  BrowserCat
  

- [](https://github.com/microsoft/playwright-cli/issues/388)
  
  
  
  Orphaned --browser chrome processes block normal Chrome on macOS · Issue #388 · microsoft/playwright-cli2026年4月29日 — When a daemon using --browser chrome ( channel: "chrome" ) dies ungracefully, the Chrome process it spawned becomes orphaned (PPID...
  
  
  GitHub
  

- [](https://www.mdsec.co.uk/2021/01/breaking-the-browser-a-tale-of-ipc-credentials-and-backdoors/)
  
  
  
  Breaking The Browser - A tale of IPC, credentials and backdoors2021年1月12日 — Like most browsers Chrome ( Google Chrome ) uses a multi-process architecture (as can be seen below):
  
  
  MDSec
  

- [](https://kashsecurity.medium.com/the-architecture-of-google-chrome-e943c20929f0)
  
  
  
  The Architecture of Google Chrome | by KAsh Security | Medium2025年8月16日 — * **Browser process** (a.k.a. the “chrome” of Chrome ( Google Chrome ) ): owns privileged capabilities and global coordination — U...
  
  
  Medium
  

關閉

停止

傳送

傳送

Turn on your Visual Search History?

Google uses its visual recognition technologies to process the images you use to search, like when you search with Google Lens. If you turn on your Visual Search History, Google will save these images from eligible Google services to your Web & App Activity when you’re signed in to your Google Account. You can learn more about this setting and which Google services save images to it at g.co/Search/VisualSearchHistory.

How visual search history is used

Your Visual Search History may be used to improve your experience on Google services, like letting you revisit your past visual searches. It may be used to develop and improve Google’s visual recognition and search technologies, as well as the Google services that use them.

When visual search history is off

If you turn this setting off, any previous Visual Search History may still be kept and used to improve Google’s visual recognition and search technologies, unless you delete it from your Web & App Activity.

Visual Search History doesn’t affect images saved by other settings, like Gemini Apps Activity.

How to manage your Visual Search History

You can view, delete, or manage your Visual Search History at activity.google.com. To download your Visual Search History, visit takeout.google.com. Images will be deleted in accordance with your Web & App Activity auto-delete settings, although some types of images may be deleted sooner.

Google uses and saves data in accordance with Google Privacy Policy.

No thanks

Turn on



[#](#)[](/setprefs?sig=0_F6SBNRGpbHUQ7rsiBjE8hzDf8II%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DChrome%2Bsubprocess%2Bdaemon%2BmacOS%2Bprocess%2Bmanagement%2Bbrowser%2Bautomation%2Bpatterns%26udm%3D50%26sei%3Dxd4OavC3KcDt1e8P9qC-uQY&hl=en&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&sei=xd4OavC3KcDt1e8P9qC-uQY&mstk=AUtExfA1lrVh7Ampj6BS3_G704N9CyWyqt6TDKZLIMeFQUpKuAOteE-eRNnUinORNpMNTH7cliWOOpZEYj1Fwei-5HYflJCpBJ_yqHbjQmou12LYMxfyqFO7fz76SU5qqHmSqNG-n2Pn85t-uLc5L7Wh95Mja9C0LASgVK0&csuir=1/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQ0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&sei=xd4OavC3KcDt1e8P9qC-uQY&mstk=AUtExfA1lrVh7Ampj6BS3_G704N9CyWyqt6TDKZLIMeFQUpKuAOteE-eRNnUinORNpMNTH7cliWOOpZEYj1Fwei-5HYflJCpBJ_yqHbjQmou12LYMxfyqFO7fz76SU5qqHmSqNG-n2Pn85t-uLc5L7Wh95Mja9C0LASgVK0&csuir=1/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQ0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&sei=xd4OavC3KcDt1e8P9qC-uQY&mstk=AUtExfA1lrVh7Ampj6BS3_G704N9CyWyqt6TDKZLIMeFQUpKuAOteE-eRNnUinORNpMNTH7cliWOOpZEYj1Fwei-5HYflJCpBJ_yqHbjQmou12LYMxfyqFO7fz76SU5qqHmSqNG-n2Pn85t-uLc5L7Wh95Mja9C0LASgVK0&csuir=1/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQ0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&sei=xd4OavC3KcDt1e8P9qC-uQY&mstk=AUtExfA1lrVh7Ampj6BS3_G704N9CyWyqt6TDKZLIMeFQUpKuAOteE-eRNnUinORNpMNTH7cliWOOpZEYj1Fwei-5HYflJCpBJ_yqHbjQmou12LYMxfyqFO7fz76SU5qqHmSqNG-n2Pn85t-uLc5L7Wh95Mja9C0LASgVK0&csuir=1/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQ0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&sei=xd4OavC3KcDt1e8P9qC-uQY&mstk=AUtExfA1lrVh7Ampj6BS3_G704N9CyWyqt6TDKZLIMeFQUpKuAOteE-eRNnUinORNpMNTH7cliWOOpZEYj1Fwei-5HYflJCpBJ_yqHbjQmou12LYMxfyqFO7fz76SU5qqHmSqNG-n2Pn85t-uLc5L7Wh95Mja9C0LASgVK0&csuir=1/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&udm=50&sei=xd4OavC3KcDt1e8P9qC-uQY&mstk=AUtExfA1lrVh7Ampj6BS3_G704N9CyWyqt6TDKZLIMeFQUpKuAOteE-eRNnUinORNpMNTH7cliWOOpZEYj1Fwei-5HYflJCpBJ_yqHbjQmou12LYMxfyqFO7fz76SU5qqHmSqNG-n2Pn85t-uLc5L7Wh95Mja9C0LASgVK0&csuir=1/search?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQ0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Chrome+subprocess+daemon+macOS+process+management+browser+automation+patterns&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwiZuoa2lsqUAxUhdvUHHd3dBOQQ0pQJegQIBhAY
[10] 我的 Google 搜尋記錄 — https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm
[11] 隱私權政策 — https://policies.google.com/privacy
[12] 服務條款 — https://policies.google.com/terms
[13] 提出依法移除要求 — https://support.google.com/legal/answer/3110420