[](https://support.google.com/websearch/answer/181196?hl=zh-HK) [10][13]

無障礙功能意見

---


如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm](https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm)

Patchright launchServer connect_over_cdp persistent browser daemon keep alive anti detection CDP patches

Here is how to connect `patchright` to a persistent, anti-detection browser daemon using Chrome DevTools Protocol (CDP) while keeping the session alive. 

Core Solution 

Launch the browser daemon via CLI with anti-detection flags, then use `patchright.chromium.connect_over_cdp()` to attach your script to that persistent instance. 

Step 1: Launch the Persistent Daemon 

Run this command in your terminal to start a background browser instance that stays open. 

bash

```
chrome --remote-debugging-port=9222 --user-data-dir="/path/to/profile" --disable-blink-features=AutomationControlled

```

請謹慎使用程式碼。

- **`--remote-debugging-port=9222`**: Opens the CDP port.
- **`--user-data-dir`**: Ensures persistence of cookies, history, and logins.
- **`--disable-blink-features=AutomationControlled`**: Removes the standard `navigator.webdriver` flag. 


Step 2: Connect via Patchright 

Use this Python structure to connect to the daemon, apply stealth patches, and prevent the script from closing the browser. 

python

```
import asyncio
from patchright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Connect to the already running daemon
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
  
        # Access the default persistent context
        context = browser.contexts[0]
  
        # Apply anti-detection CDP patches at runtime
        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)
  
        # Execute scraping tasks
        await page.goto("https://sannysoft.com")
        print("Page title:", await page.title())
  
        # KEEP ALIVE: Do not close browser or context.
        # Infinite loop keeps the script attached to the daemon.
        print("Daemon connection alive. Press Ctrl+C to detach script.")
        while True:
            await asyncio.sleep(3600)

try:
    asyncio.run(run())
except KeyboardInterrupt:
    print("Detached from daemon. Browser remains running.")

```

請謹慎使用程式碼。

Critical Anti-Detection CDP Patches 

To pass advanced fingerprinting tests (like Cloudflare or Akamai) over CDP, evaluate these settings: 

- **Viewport & User Agent**: Match your real hardware specifications exactly.
- **Fingerprint Evasion**: Use `add_init_script` to mask WebGL, Canvas, and audio fingerprints.
- **No `launch_server`**: Avoid `p.chromium.launch_server()` if you want true multi-process independence, as it binds the browser lifecycle to the parent script. 


To optimize this setup, tell me: 

- What **specific bot detection** (Cloudflare, PerimeterX, etc.) are you targeting?
- Do you need to run **multiple isolated profiles** simultaneously on this daemon?
- What **operating system** is hosting your browser daemon? 


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

- [](https://github.com/NousResearch/hermes-agent/issues/21532)
  
  
  
  Bug: CDP Browser Mode Does Not Close Tabs on Cleanup · Issue #21532 · NousResearch/hermes-agent2026年5月8日 — Verification Steps Start Chrome with remote debugging: google-chrome --remote-debugging-port=9222 Run multiple browser_navigate ca...
  
  
  GitHub
  

- [](https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/)
  
  
  
  From Puppeteer stealth to Nodriver: How anti-detect frameworks evolved to evade bot detection2025年6月11日 — Launch Chrome with --disable-blink-features=AutomationControlled to suppress the navigator. webdriver flag.
  
  
  blog.castle.io
  

- [](https://www.zenrows.com/blog/patchright)
  
  
  
  How to Scrape with Patchright and Avoid Detection2025年11月24日 — Patchright is available in both Python and Node. js, with installation guides for each. So, whether you've set up your Playwright ...
  
  
  ZenRows
  

- [](https://github.com/NousResearch/hermes-agent/issues/21532)
  
  
  
  Bug: CDP Browser Mode Does Not Close Tabs on Cleanup · Issue #21532 · NousResearch/hermes-agent2026年5月8日 — Verification Steps Start Chrome with remote debugging: google-chrome --remote-debugging-port=9222 Run multiple browser_navigate ca...
  
  
  GitHub
  

- [](https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/)
  
  
  
  From Puppeteer stealth to Nodriver: How anti-detect frameworks evolved to evade bot detection2025年6月11日 — Launch Chrome with --disable-blink-features=AutomationControlled to suppress the navigator. webdriver flag.
  
  
  blog.castle.io
  

- [](https://www.zenrows.com/blog/patchright)
  
  
  
  How to Scrape with Patchright and Avoid Detection2025年11月24日 — Patchright is available in both Python and Node. js, with installation guides for each. So, whether you've set up your Playwright ...
  
  
  ZenRows
  

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



[#](#)[](/setprefs?sig=0_F_wM3AEkz5DM-1J0f2MS1Cx2yNU%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DPatchright%2BlaunchServer%2Bconnect_over_cdp%2Bpersistent%2Bbrowser%2Bdaemon%2Bkeep%2Balive%2Banti%2Bdetection%2BCDP%2Bpatches%26udm%3D50%26sei%3DcuUOariXNqzQ2roP0qiu8Q0&hl=en&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4QhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4QiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&sei=cuUOariXNqzQ2roP0qiu8Q0&mstk=AUtExfCy7YmmLYVbbFbz8SNvkBIAMbyoepAVtn0aqc3ZntWT34msJZZQYpTlM9prMGs0n3X1b8ZAu2KjLLnS8vutks1E9hkAINtOp05D5TOP0kJYn8g0odDeJUblBI4Gx5Cqy9omVqkZmqpKl-H9sbpP4hIy8c-xCHOa_tc&csuir=1/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4Q0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&sei=cuUOariXNqzQ2roP0qiu8Q0&mstk=AUtExfCy7YmmLYVbbFbz8SNvkBIAMbyoepAVtn0aqc3ZntWT34msJZZQYpTlM9prMGs0n3X1b8ZAu2KjLLnS8vutks1E9hkAINtOp05D5TOP0kJYn8g0odDeJUblBI4Gx5Cqy9omVqkZmqpKl-H9sbpP4hIy8c-xCHOa_tc&csuir=1/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4Q0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&sei=cuUOariXNqzQ2roP0qiu8Q0&mstk=AUtExfCy7YmmLYVbbFbz8SNvkBIAMbyoepAVtn0aqc3ZntWT34msJZZQYpTlM9prMGs0n3X1b8ZAu2KjLLnS8vutks1E9hkAINtOp05D5TOP0kJYn8g0odDeJUblBI4Gx5Cqy9omVqkZmqpKl-H9sbpP4hIy8c-xCHOa_tc&csuir=1/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4Q0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&sei=cuUOariXNqzQ2roP0qiu8Q0&mstk=AUtExfCy7YmmLYVbbFbz8SNvkBIAMbyoepAVtn0aqc3ZntWT34msJZZQYpTlM9prMGs0n3X1b8ZAu2KjLLnS8vutks1E9hkAINtOp05D5TOP0kJYn8g0odDeJUblBI4Gx5Cqy9omVqkZmqpKl-H9sbpP4hIy8c-xCHOa_tc&csuir=1/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4Q0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&sei=cuUOariXNqzQ2roP0qiu8Q0&mstk=AUtExfCy7YmmLYVbbFbz8SNvkBIAMbyoepAVtn0aqc3ZntWT34msJZZQYpTlM9prMGs0n3X1b8ZAu2KjLLnS8vutks1E9hkAINtOp05D5TOP0kJYn8g0odDeJUblBI4Gx5Cqy9omVqkZmqpKl-H9sbpP4hIy8c-xCHOa_tc&csuir=1/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&udm=50&sei=cuUOariXNqzQ2roP0qiu8Q0&mstk=AUtExfCy7YmmLYVbbFbz8SNvkBIAMbyoepAVtn0aqc3ZntWT34msJZZQYpTlM9prMGs0n3X1b8ZAu2KjLLnS8vutks1E9hkAINtOp05D5TOP0kJYn8g0odDeJUblBI4Gx5Cqy9omVqkZmqpKl-H9sbpP4hIy8c-xCHOa_tc&csuir=1/search?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4Q0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Patchright+launchServer+connect_over_cdp+persistent+browser+daemon+keep+alive+anti+detection+CDP+patches&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwja5IblnMqUAxV2h1YBHeAGHL4Q0pQJegQIBhAY
[10] 我的 Google 搜尋記錄 — https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm
[11] 隱私權政策 — https://policies.google.com/privacy
[12] 服務條款 — https://policies.google.com/terms
[13] 提出依法移除要求 — https://support.google.com/legal/answer/3110420