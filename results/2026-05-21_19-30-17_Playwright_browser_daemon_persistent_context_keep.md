[](https://support.google.com/websearch/answer/181196?hl=zh-HK) [10]

無障礙功能意見

---

如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm](https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm)

Playwright browser daemon persistent context keep alive separate process anti detection CDP patches best practice 2025

**搜尋中**

To build an undetectable, long-running web automation framework in 2026, relying on basic `playwright-stealth` or stock `launch_persistent_context` is no longer enough. Modern anti-bot systems (like Cloudflare, Akamai, and Kasada) easily trace execution loops back to Playwright by catching specific Chrome DevTools Protocol (CDP) interactions. [](https://rebrowser.net/blog/how-to-fix-runtime-enable-cdp-detection-of-puppeteer-playwright-and-other-automation-libraries)

The architecture detailed below outlines the **2026 production-grade best practices** to implement a decoupled browser daemon with patched anti-detection mechanisms. 

---


1. The Core Architecture: Decoupled Daemon Process 

To ensure your browser context remains alive across script restarts and functions as a stable daemon, **never let your application process manage the browser lifecycle directly**. You must separate the browser execution into an independent background process and connect via CDP. [](https://stackoverflow.com/questions/65802677/how-to-keep-browser-opening-by-the-end-of-the-code-running-with-playwright-pytho)

```
┌─────────────────────────────────┐
│     Independent Daemon Process   │ (Keeps session cookies, state,
│    (Spawned via Systemd/PM2)    │  and local storage alive)
└────────────────┬────────────────┘
                 │ --remote-debugging-port=9222
                 ▼
┌─────────────────────────────────┐
│     Playwright Client Script    │ (Connects, runs ephemeral automation,
│  (Connects & Disconnects over CDP)│  disconnects without killing browser)
└─────────────────────────────────┘

```

Step A: Spawning the Standalone Persistent Daemon 

Launch Chrome through your operating system's process manager (like `PM2` or `systemd`) using a dedicated `user-data-dir`. Use these exact command-line arguments to minimize the initial automation signature: [](https://medium.com/@Gayathri_krish/mastering-persistent-sessions-in-playwright-keep-your-logins-alive-8e4e0fd52751)

bash

```
# Launching the persistent browser daemon in the background
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/var/lib/browser-profiles/profile_1" \
  --no-first-run \
  --no-default-browser-check \
  --password-store=basic \
  --headless=new

```

請謹慎使用程式碼。

*Note: Ensure `--headless=new` (native headless) is used rather than the old legacy headless, which lacks standard browser features and instantly trips anti-bot scripts.* 

Step B: Client Connection Best Practice 

Your automation scripts connect to this alive daemon instance using `connectOverCDP`. When your script finishes executing, closing the context **will not close the browser process**, leaving it ready for subsequent tasks. [](https://playwright.dev/docs/api/class-browsertype)

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



[#](#)[](/setprefs?sig=0_CEOU2x_iXcik351rQSznsu6TTJM%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DPlaywright%2Bbrowser%2Bdaemon%2Bpersistent%2Bcontext%2Bkeep%2Balive%2Bseparate%2Bprocess%2Banti%2Bdetection%2BCDP%2Bpatches%2Bbest%2Bpractice%2B2025%26udm%3D50%26sei%3DxOwOatfaAvfi2roPlJeZuQs&hl=en&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&sei=xOwOatfaAvfi2roPlJeZuQs&mstk=AUtExfDB25vnGHFDxvYSSNGi5bSjjnhwtbbAHLG9_gW6ckZbpJX80gz6laWSTBgCTHkHDzEYikdsMhGXSYQHix1I0x7Vnva_qqgPOQ0Kcr90LJKt5s8HpoJpbXOl68VMW2xsQa0PZDJzkFZVsjTFzNTMzHPdyGG0xflDiNI&csuir=1/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQ0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&sei=xOwOatfaAvfi2roPlJeZuQs&mstk=AUtExfDB25vnGHFDxvYSSNGi5bSjjnhwtbbAHLG9_gW6ckZbpJX80gz6laWSTBgCTHkHDzEYikdsMhGXSYQHix1I0x7Vnva_qqgPOQ0Kcr90LJKt5s8HpoJpbXOl68VMW2xsQa0PZDJzkFZVsjTFzNTMzHPdyGG0xflDiNI&csuir=1/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQ0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&sei=xOwOatfaAvfi2roPlJeZuQs&mstk=AUtExfDB25vnGHFDxvYSSNGi5bSjjnhwtbbAHLG9_gW6ckZbpJX80gz6laWSTBgCTHkHDzEYikdsMhGXSYQHix1I0x7Vnva_qqgPOQ0Kcr90LJKt5s8HpoJpbXOl68VMW2xsQa0PZDJzkFZVsjTFzNTMzHPdyGG0xflDiNI&csuir=1/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQ0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&sei=xOwOatfaAvfi2roPlJeZuQs&mstk=AUtExfDB25vnGHFDxvYSSNGi5bSjjnhwtbbAHLG9_gW6ckZbpJX80gz6laWSTBgCTHkHDzEYikdsMhGXSYQHix1I0x7Vnva_qqgPOQ0Kcr90LJKt5s8HpoJpbXOl68VMW2xsQa0PZDJzkFZVsjTFzNTMzHPdyGG0xflDiNI&csuir=1/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQ0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&sei=xOwOatfaAvfi2roPlJeZuQs&mstk=AUtExfDB25vnGHFDxvYSSNGi5bSjjnhwtbbAHLG9_gW6ckZbpJX80gz6laWSTBgCTHkHDzEYikdsMhGXSYQHix1I0x7Vnva_qqgPOQ0Kcr90LJKt5s8HpoJpbXOl68VMW2xsQa0PZDJzkFZVsjTFzNTMzHPdyGG0xflDiNI&csuir=1/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&udm=50&sei=xOwOatfaAvfi2roPlJeZuQs&mstk=AUtExfDB25vnGHFDxvYSSNGi5bSjjnhwtbbAHLG9_gW6ckZbpJX80gz6laWSTBgCTHkHDzEYikdsMhGXSYQHix1I0x7Vnva_qqgPOQ0Kcr90LJKt5s8HpoJpbXOl68VMW2xsQa0PZDJzkFZVsjTFzNTMzHPdyGG0xflDiNI&csuir=1/search?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQ0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Playwright+browser+daemon+persistent+context+keep+alive+separate+process+anti+detection+CDP+patches+best+practice+2025&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwi4wJ_io8qUAxUbslYBHT6sH7IQ0pQJegQIBhAY
[10] 我的 Google 搜尋記錄 — https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm