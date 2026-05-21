[](https://support.google.com/websearch/answer/181196?hl=zh-HK) [10][13]

無障礙功能意見

---


如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm](https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm)

Playwright Puppeteer detach browser process keep alive CDP debugging port reconnect different script anti detection

Here is how to launch a browser, detach it, keep it alive, and reconnect to it later using its Chrome DevTools Protocol (CDP) port in both Playwright and Puppeteer, along with anti-detection strategies. 

1. Launch & Detach (Script A) 

To keep the browser alive after the script exits, you must use `launchPersistentContext` (Playwright) or set `detached: true` in `child_process` if launching manually. The cleanest way is to use native flags that prevent the browser from closing when the parent process dies. 

Playwright (Python) 

python

```
import subprocess
import time

# Launch Chrome via CLI to ensure it completely detaches from the script process
cmd = [
    "google-chrome",  # Or path to your chrome binary
    "--remote-debugging-port=9222",
    "--user-data-dir=/path/to/profile",
    "--no-first-run",
    "--no-default-browser-check"
]
# Start process independently
subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Browser launched on port 9222. Script A can now exit safely.")

```

請謹慎使用程式碼。

Puppeteer (Node.js) 

javascript

```
const { spawn } = require('child_process');

const chrome = spawn('google-chrome', [
  '--remote-debugging-port=9222',
  '--user-data-dir=/path/to/profile'
], {
  detached: true, // Key flag to keep it alive
  stdio: 'ignore'
});

chrome.unref(); // Allows the Node process to exit independently
console.log("Browser detached. Script A exiting.");
process.exit();

```

請謹慎使用程式碼。

---


2. Reconnect From Another Script (Script B) 

Once the browser is running on port `9222`, any separate script can connect to it using the CDP endpoint URL. 

Playwright (Python) 

python

```
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Connect directly using the local CDP endpoint
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
  
    # Access existing pages or create a new one
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else context.new_page()
  
    page.goto("https://example.com")
    print(page.title())
  
    # Crucial: Disconnect instead of close to keep browser alive
    browser.disconnect()

```

請謹慎使用程式碼。

Puppeteer (Node.js) 

javascript

```
const puppeteer = require('puppeteer');
const axios = require('axios'); // To fetch the WebSocket URL

async function reconnect() {
  # Fetch the active WebSocket URL from the browser local endpoint
  const response = await axios.get('http://localhost:9222/json/version');
  const wsChromeEndpointUrl = response.data.webSocketDebuggerUrl;

  const browser = await puppeteer.connect({
    browserWSEndpoint: wsChromeEndpointUrl,
  });

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();
  
  await page.goto('https://example.com');
  
  # Crucial: Disconnect instead of close
  browser.disconnect();
}
reconnect();

```

請謹慎使用程式碼。

---


3. Anti-Detection Strategies 

Connecting via CDP bypasses standard automation signatures, but anti-bot systems (Cloudflare, Kasada) can easily detect raw CDP setups due to default arguments and missing browser properties. 

- **Do Not Use Default Playwright/Puppeteer Binaries**: Always point to a real, installed stable version of Google Chrome or Brave Browser using the `executablePath` or CLI launch.
- **Remove Automation Flags**: Ensure your launch command does **NOT** contain `--enable-automation` or `--blink-settings=automationControlled=true`. These flags instantly flip `navigator.webdriver` to `true`.
- **Use Stealth Plugins**:
  * For **Puppeteer**: Use `puppeteer-extra-plugin-stealth`.
  * For **Playwright**: Use `playwright-stealth` or the `camoufox` library.
- **Match the User Profile**: Always supply a `--user-data-dir`. A persistent profile retains history, cookies, and local storage, making the browser look organic.
- **Randomize Viewports**: Do not use the default headless viewport sizes (like 800x600). Set explicit, common screen resolutions (e.g., 1920x1080). 


If you need help setting up the stealth configurations, let me know **which language** (Python or Node.js) and **which framework** (Playwright or Puppeteer) you prefer to target. 

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

- [](https://playwright.dev/python/docs/api/class-browsertype)
  
  
  
  BrowserTypeconnect_over_cdp This method attaches Playwright to an existing browser instance using the Chrome DevTools Protocol. The default b...
  
  
  Playwright
  

- [](https://docs.browserless.io/browserql/session-management/puppeteer-playwright)
  
  
  
  Puppeteer & Playwright | Browserless DocumentationThe browserWSEndpoint from the response connects to any library that supports the Chrome DevTools Protocol (CDP). This includes Pu...
  
  
  Browserless Docs
  

- [](https://scrapingant.com/blog/playwright-scraping-undetectable)
  
  
  
  How to Make Playwright Scraping Undetectable2024年9月7日 — When automation tools use CDP, they send commands directly to the browser to perform actions. Anti-bot systems can now detect when...
  
  
  ScrapingAnt
  

- [](https://kameleo.io/blog/how-to-bypass-cloudflare-with-playwright)
  
  
  
  How to Bypass Cloudflare with Playwright in 20252025年7月3日 — Result: You're likely to hit Cloudflare's anti-bot defenses. Let's explore advanced techniques to overcome that.
  
  
  Kameleo
  

- [](https://blog.devgenius.io/automating-recaptcha-solving-with-puppeteer-a-step-by-step-guide-17d3269d9c3d)
  
  
  
  Automating reCAPTCHA Solving with Puppeteer: A Step-by-Step Guide2023年11月15日 — Browser Automation Setup: Incorporate the stealth plugin into Puppeteer's initialization to conceal the automation. This is crucia...
  
  
  Dev Genius
  

- [](https://www.scrapingdog.com/blog/puppeteer-stealth/)
  
  
  
  Puppeteer Stealth Tutorial: How To Use & Setup (+Alternatives)2025年3月15日 — Puppeteer stealth plugin, or puppeteer-extra-plugin-stealth is a plugin for Puppeteer that aims to make it significantly harder fo...
  
  
  Scrapingdog
  

- [](https://www.zenrows.com/blog/playwright-403)
  
  
  
  How to Solve Playwright 403 Forbidden Error2024年4月2日 — 5. Use Playwright Stealth Extension Playwright Stealth is a plugin that aims to extend Playwright functionality with the ability t...
  
  
  ZenRows
  

- [](https://www.browserless.io/blog/anti-detection-techniques-2026-guide)
  
  
  
  Anti-Detection Techniques in 2026 | Developer Guide to Modern Detection2026年3月13日 — Treating profiles as stateful runtime objects is more effective. Persistent profiles allow cookies and storage to evolve naturally...
  
  
  Browserless
  

- [](https://www.capsolver.com/blog/Extension/aws-captcha-solver-puppeteer)
  
  
  
  How to Solve AWS Captcha Using Puppeteer [Javascript] with CapSolver Extension2023年11月29日 — V. AI Search Automation Best Practices: Beyond the CAPTCHA Best Practice Description Relevance to Puppeteer/JS Session Management ...
  
  
  CapSolver
  

- [](https://playwright.dev/python/docs/api/class-browsertype)
  
  
  
  BrowserTypeconnect_over_cdp This method attaches Playwright to an existing browser instance using the Chrome DevTools Protocol. The default b...
  
  
  Playwright
  

- [](https://docs.browserless.io/browserql/session-management/puppeteer-playwright)
  
  
  
  Puppeteer & Playwright | Browserless DocumentationThe browserWSEndpoint from the response connects to any library that supports the Chrome DevTools Protocol (CDP). This includes Pu...
  
  
  Browserless Docs
  

- [](https://scrapingant.com/blog/playwright-scraping-undetectable)
  
  
  
  How to Make Playwright Scraping Undetectable2024年9月7日 — When automation tools use CDP, they send commands directly to the browser to perform actions. Anti-bot systems can now detect when...
  
  
  ScrapingAnt
  

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



[#](#)[](/setprefs?sig=0_Hnwx6_R6bzi2aryw3hJMxAr-Yms%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DPlaywright%2BPuppeteer%2Bdetach%2Bbrowser%2Bprocess%2Bkeep%2Balive%2BCDP%2Bdebugging%2Bport%2Breconnect%2Bdifferent%2Bscript%2Banti%2Bdetection%26udm%3D50%26sei%3DfuUOatjeLOKPrfcPkoXxIA&hl=en&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&sei=fuUOatjeLOKPrfcPkoXxIA&mstk=AUtExfCDhLt6U5v0S2XseXLr-0jFdabSfKor20VPnFHy06DHDra6y00TNjG68_2Q6URlvLdbud_tGSIyrs9TUodfYmCzVWf4uvHeyPv1X1XjQE98cmITjsqCGU3W-SgJ4p-YewEY7-I0J5nVEqy-4UCUipygK5LpiltwSuQ&csuir=1/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQ0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&sei=fuUOatjeLOKPrfcPkoXxIA&mstk=AUtExfCDhLt6U5v0S2XseXLr-0jFdabSfKor20VPnFHy06DHDra6y00TNjG68_2Q6URlvLdbud_tGSIyrs9TUodfYmCzVWf4uvHeyPv1X1XjQE98cmITjsqCGU3W-SgJ4p-YewEY7-I0J5nVEqy-4UCUipygK5LpiltwSuQ&csuir=1/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQ0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&sei=fuUOatjeLOKPrfcPkoXxIA&mstk=AUtExfCDhLt6U5v0S2XseXLr-0jFdabSfKor20VPnFHy06DHDra6y00TNjG68_2Q6URlvLdbud_tGSIyrs9TUodfYmCzVWf4uvHeyPv1X1XjQE98cmITjsqCGU3W-SgJ4p-YewEY7-I0J5nVEqy-4UCUipygK5LpiltwSuQ&csuir=1/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQ0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&sei=fuUOatjeLOKPrfcPkoXxIA&mstk=AUtExfCDhLt6U5v0S2XseXLr-0jFdabSfKor20VPnFHy06DHDra6y00TNjG68_2Q6URlvLdbud_tGSIyrs9TUodfYmCzVWf4uvHeyPv1X1XjQE98cmITjsqCGU3W-SgJ4p-YewEY7-I0J5nVEqy-4UCUipygK5LpiltwSuQ&csuir=1/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQ0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&sei=fuUOatjeLOKPrfcPkoXxIA&mstk=AUtExfCDhLt6U5v0S2XseXLr-0jFdabSfKor20VPnFHy06DHDra6y00TNjG68_2Q6URlvLdbud_tGSIyrs9TUodfYmCzVWf4uvHeyPv1X1XjQE98cmITjsqCGU3W-SgJ4p-YewEY7-I0J5nVEqy-4UCUipygK5LpiltwSuQ&csuir=1/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&udm=50&sei=fuUOatjeLOKPrfcPkoXxIA&mstk=AUtExfCDhLt6U5v0S2XseXLr-0jFdabSfKor20VPnFHy06DHDra6y00TNjG68_2Q6URlvLdbud_tGSIyrs9TUodfYmCzVWf4uvHeyPv1X1XjQE98cmITjsqCGU3W-SgJ4p-YewEY7-I0J5nVEqy-4UCUipygK5LpiltwSuQ&csuir=1/search?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQ0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Playwright+Puppeteer+detach+browser+process+keep+alive+CDP+debugging+port+reconnect+different+script+anti+detection&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwjfsdrqnMqUAxUmm1YBHaKdJPMQ0pQJegQIBhAY
[10] 我的 Google 搜尋記錄 — https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm
[11] 隱私權政策 — https://policies.google.com/privacy
[12] 服務條款 — https://policies.google.com/terms
[13] 提出依法移除要求 — https://support.google.com/legal/answer/3110420