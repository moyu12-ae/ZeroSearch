[](https://support.google.com/websearch/answer/181196?hl=zh-HK)

無障礙功能意見

---


如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[查看我的](https://myactivity.google.com/search-services/history/search?product=83&utm_source=aim&utm_campaign=aim_tm) [10]

Chrome remote debugging port security localhost CDP WebSocket authentication hardening

**搜尋中**

**預設情況下，Chrome DevTools Protocol (CDP) 遠端偵錯通訊協定完全沒有內建身分驗證機制。** [](https://stackoverflow.com/questions/40538197/chrome-remote-debugging-from-another-machine)

這代表任何能夠存取該連接埠（Port）的本地程式，都可以透過 WebSocket 注入惡意 JavaScript、竊取憑證與所有網頁的 Cookie。為了防範惡意程式與資訊竊取軟體（Infostealers），Google 和安全社群已針對 `localhost` 的 CDP 安全性進行了大幅度收緊與強化。 [](https://embracethered.com/blog/posts/2020/chrome-spy-remote-control/)

以下為確保 `localhost` 遠端偵錯安全的四大防禦層次與最佳實踐： 

---


1. Chrome 官方安全機制：限制預設使用者目錄 

為因應日益嚴重的憑證竊取攻擊，**Chrome 自 v136+ 版本起，已禁止對「預設使用者目錄（Default User Data Dir）」啟用 `--remote-debugging-port`。** [](https://github.com/vercel-labs/agent-browser/issues/870)

- **安全行為**：如果您試圖在平時使用的主要 Chrome 瀏覽器上直接啟用偵錯埠，Chrome 會直接**靜態無視該參數**，以防惡意 LNK 檔或惡意軟體在背景默默控制您的日常瀏覽器。
- **正確做法**：必須搭配全新的、隔離的資料目錄（User Data Directory）才能順利開啟偵錯埠。
  
  
  
  
  bash
  

```
# 必須指定一個完全獨立的、非標準的配置目錄來進行隔離
google-chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-isolated-profile

```
  
  請謹慎使用程式碼。 [](https://developer.chrome.com/blog/remote-debugging-port)

2. 網路層強化（WebSocket 來源檢查） 

當開啟偵錯埠後，本機上運行的任何惡意網頁（透過 DNS Rebinding 攻擊）都可能試圖與您的 CDP WebSocket 建立連線。 [](https://issues.chromium.org/issues/40063053)

- **強制限制來源（Origin）**：啟動時務必顯式限定允許連接 CDP 的 Host/Origin，防止瀏覽器內的惡意分頁跨來源操縱 CDP。
  
  
  
  
  bash
  

```
google-chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-profile --remote-allow-origins="http://localhost:9222,http://127.0.0.1:9222"

```
  
  請謹慎使用程式碼。

- **絕對不要使用的危險參數**：嚴禁使用 `--remote-allow-origins=*`，這會讓本機任何網站都能輕易接管您的 CDP。 [](https://issues.chromium.org/issues/40261787)


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



[#](#)[](/setprefs?sig=0_FLCkRkV9ZZZe1pqhXrOJrxWJK8Q%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DChrome%2Bremote%2Bdebugging%2Bport%2Bsecurity%2Blocalhost%2BCDP%2BWebSocket%2Bauthentication%2Bhardening%26udm%3D50%26sei%3D6d4OaunPEJne1e8Pw5ad4Ak&hl=en&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0QhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0QiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&sei=6d4OaunPEJne1e8Pw5ad4Ak&mstk=AUtExfDdeBF321bvVA3pzAsnJMkb07e5LsBp5Tmw4ppVya01sT8sXhCGKnsNUklI1ATTqDu5Tc8yaeG-k0pQojst4y5bKtRfL5F7ELIRuRmVM7benSLbrHlirOIyRiBGtBnDfwgji7kgxKAkcZ0bSpwolvsH_U_QMAX2lW4&csuir=1/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0Q0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&sei=6d4OaunPEJne1e8Pw5ad4Ak&mstk=AUtExfDdeBF321bvVA3pzAsnJMkb07e5LsBp5Tmw4ppVya01sT8sXhCGKnsNUklI1ATTqDu5Tc8yaeG-k0pQojst4y5bKtRfL5F7ELIRuRmVM7benSLbrHlirOIyRiBGtBnDfwgji7kgxKAkcZ0bSpwolvsH_U_QMAX2lW4&csuir=1/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0Q0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&sei=6d4OaunPEJne1e8Pw5ad4Ak&mstk=AUtExfDdeBF321bvVA3pzAsnJMkb07e5LsBp5Tmw4ppVya01sT8sXhCGKnsNUklI1ATTqDu5Tc8yaeG-k0pQojst4y5bKtRfL5F7ELIRuRmVM7benSLbrHlirOIyRiBGtBnDfwgji7kgxKAkcZ0bSpwolvsH_U_QMAX2lW4&csuir=1/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0Q0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&sei=6d4OaunPEJne1e8Pw5ad4Ak&mstk=AUtExfDdeBF321bvVA3pzAsnJMkb07e5LsBp5Tmw4ppVya01sT8sXhCGKnsNUklI1ATTqDu5Tc8yaeG-k0pQojst4y5bKtRfL5F7ELIRuRmVM7benSLbrHlirOIyRiBGtBnDfwgji7kgxKAkcZ0bSpwolvsH_U_QMAX2lW4&csuir=1/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0Q0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&sei=6d4OaunPEJne1e8Pw5ad4Ak&mstk=AUtExfDdeBF321bvVA3pzAsnJMkb07e5LsBp5Tmw4ppVya01sT8sXhCGKnsNUklI1ATTqDu5Tc8yaeG-k0pQojst4y5bKtRfL5F7ELIRuRmVM7benSLbrHlirOIyRiBGtBnDfwgji7kgxKAkcZ0bSpwolvsH_U_QMAX2lW4&csuir=1/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&udm=50&sei=6d4OaunPEJne1e8Pw5ad4Ak&mstk=AUtExfDdeBF321bvVA3pzAsnJMkb07e5LsBp5Tmw4ppVya01sT8sXhCGKnsNUklI1ATTqDu5Tc8yaeG-k0pQojst4y5bKtRfL5F7ELIRuRmVM7benSLbrHlirOIyRiBGtBnDfwgji7kgxKAkcZ0bSpwolvsH_U_QMAX2lW4&csuir=1/search?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0Q0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Chrome+remote+debugging+port+security+localhost+CDP+WebSocket+authentication+hardening&newwindow=1&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwjt0__GlsqUAxWin68BHWKZJp0Q0pQJegQIBhAY
[10] 查看我的 AI 模式記錄 — https://myactivity.google.com/search-services/history/search?product=83&utm_source=aim&utm_campaign=aim_tm