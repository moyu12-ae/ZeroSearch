[](https://support.google.com/websearch/answer/181196?hl=zh-HK) [10]

無障礙功能意見

---


如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm](https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm)

Playwright launch_persistent_context CDP port connect_over_cdp browser detach keep alive single process

在 Playwright 中，結合 `launch_persistent_context`、CDP（Chrome DevTools Protocol）端口、`connect_over_cdp`、獨立進程（Single Process）以及保持瀏覽器不關閉（Detach / Keep Alive）是一套進階且強大的自動化架構。這通常用於**接管現有瀏覽器**或**建立一個可持續重用的瀏覽器後台服務**。 

以下是完整的實作邏輯與代碼範例： 

核心架構邏輯 

1. **啟動端（服務進程）**：使用 `launch_persistent_context` 啟動一個帶有固定 `args=['--remote-debugging-port=9222']` 的 Chromium 獨立進程，並開啟使用者數據目錄（UserDataDir）以儲存登入狀態。
2. **連線端（控制腳本）**：在另一個腳本或同腳本的後續邏輯中，使用 `connect_over_cdp('http://localhost:9222')` 連接並控制該瀏覽器。
3. **保持存活（Keep Alive）**：不要在啟動端調用 `context.close()` 或 `browser.close()`。 


---


實作代碼範例 (Python) 

步驟 1：啟動持久化 CDP 瀏覽器服務 

運行此腳本會單獨啟動一個 Chromium 進程，並將其懸掛（Keep Alive）在後台供隨時連線。 

python

```
import asyncio
from playwright.async_api import async_playwright

async def launch_backend_browser():
    async with async_playwright() as p:
        # 指定使用者數據路徑，達成持久化（Cookies, 登入狀態）
        user_data_dir = "./chromium_user_data"
  
        print("正在啟動獨立瀏覽器進程...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,  # 有頭模式方便觀察，也可設為 True
            args=[
                '--remote-debugging-port=9222',  # 開放 CDP 端口
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
  
        print("瀏覽器已成功啟動並監聽 CDP 端口 9222。")
        print("請勿關閉此進程以保持瀏覽器存活 (Keep Alive)...")
  
        # 無限循環保持進程存活，不觸發 context.close()
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(launch_backend_browser())
    except KeyboardInterrupt:
        print("後台瀏覽器服務已手動關閉。")

```

請謹慎使用程式碼。

步驟 2：使用 `connect_over_cdp` 接管並控制瀏覽器 

在**另一個獨立的腳本或終端**中運行以下代碼。它會直接連入上述 9222 端口，接管並操作同一個瀏覽器實例。 

python

```
import asyncio
from playwright.async_api import async_playwright

async def control_existing_browser():
    async with async_playwright() as p:
        print("正在連線至 CDP 端口 9222...")
        # 連接現有的瀏覽器進程
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
  
        # 獲取當前的 contexts（launch_persistent_context 預設會有一個 context）
        context = browser.contexts[0]
  
        # 打開新分頁
        page = await context.new_page()
        await page.goto("https://example.com")
        print(f"當前頁面標題: {await page.title()}")
  
        # 關閉分頁，但【不要】關閉 browser 或 context，以達成 Detach（分離）
        await page.close()
        print("操作完成，已與瀏覽器斷開連接（瀏覽器將保持在後台運行）。")

if __name__ == "__main__":
    asyncio.run(control_existing_browser())

```

請謹慎使用程式碼。

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



[#](#)[](/setprefs?sig=0_dKNzFEBwOMORHEbBogHrDZEM7is%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DPlaywright%2Blaunch_persistent_context%2BCDP%2Bport%2Bconnect_over_cdp%2Bbrowser%2Bdetach%2Bkeep%2Balive%2Bsingle%2Bprocess%26udm%3D50%26sei%3D2uwOariyO4OLvr0PltntyAY&hl=en&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8QhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8QiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&sei=2uwOariyO4OLvr0PltntyAY&mstk=AUtExfAieg5qqQk5ADhyTrK9rW0yT1_zX30geJjNQEKoWVmMTC9vZ_PEbMj7An8VxJjV-3uSwPWP3Rg4-T9dG6sUcX1XHYbBtHz1P7QiJqfZ68NeEIxaoils0rF1t_1QENqWrJsN2MXMsx1niHWHkjF3S_igUIp4V18Wrx0&csuir=1/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8Q0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&sei=2uwOariyO4OLvr0PltntyAY&mstk=AUtExfAieg5qqQk5ADhyTrK9rW0yT1_zX30geJjNQEKoWVmMTC9vZ_PEbMj7An8VxJjV-3uSwPWP3Rg4-T9dG6sUcX1XHYbBtHz1P7QiJqfZ68NeEIxaoils0rF1t_1QENqWrJsN2MXMsx1niHWHkjF3S_igUIp4V18Wrx0&csuir=1/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8Q0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&sei=2uwOariyO4OLvr0PltntyAY&mstk=AUtExfAieg5qqQk5ADhyTrK9rW0yT1_zX30geJjNQEKoWVmMTC9vZ_PEbMj7An8VxJjV-3uSwPWP3Rg4-T9dG6sUcX1XHYbBtHz1P7QiJqfZ68NeEIxaoils0rF1t_1QENqWrJsN2MXMsx1niHWHkjF3S_igUIp4V18Wrx0&csuir=1/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8Q0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&sei=2uwOariyO4OLvr0PltntyAY&mstk=AUtExfAieg5qqQk5ADhyTrK9rW0yT1_zX30geJjNQEKoWVmMTC9vZ_PEbMj7An8VxJjV-3uSwPWP3Rg4-T9dG6sUcX1XHYbBtHz1P7QiJqfZ68NeEIxaoils0rF1t_1QENqWrJsN2MXMsx1niHWHkjF3S_igUIp4V18Wrx0&csuir=1/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8Q0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&sei=2uwOariyO4OLvr0PltntyAY&mstk=AUtExfAieg5qqQk5ADhyTrK9rW0yT1_zX30geJjNQEKoWVmMTC9vZ_PEbMj7An8VxJjV-3uSwPWP3Rg4-T9dG6sUcX1XHYbBtHz1P7QiJqfZ68NeEIxaoils0rF1t_1QENqWrJsN2MXMsx1niHWHkjF3S_igUIp4V18Wrx0&csuir=1/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&udm=50&sei=2uwOariyO4OLvr0PltntyAY&mstk=AUtExfAieg5qqQk5ADhyTrK9rW0yT1_zX30geJjNQEKoWVmMTC9vZ_PEbMj7An8VxJjV-3uSwPWP3Rg4-T9dG6sUcX1XHYbBtHz1P7QiJqfZ68NeEIxaoils0rF1t_1QENqWrJsN2MXMsx1niHWHkjF3S_igUIp4V18Wrx0&csuir=1/search?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8Q0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Playwright+launch_persistent_context+CDP+port+connect_over_cdp+browser+detach+keep+alive+single+process&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwih2ZXto8qUAxVUh68BHVXCNM8Q0pQJegQIBhAY
[10] 我的 Google 搜尋記錄 — https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm