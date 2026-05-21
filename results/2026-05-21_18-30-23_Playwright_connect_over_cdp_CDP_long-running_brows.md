[](https://support.google.com/websearch/answer/181196?hl=zh-HK) [10]

無障礙功能意見

---


如要存取記錄及其他資訊，  
請登入帳戶

？

你之後無法再查看這些回覆內容

[https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm](https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm)

Playwright connect_over_cdp CDP long-running browser connection reliability pitfalls 2025

**搜尋中**

使用 Playwright 的 `connect_over_cdp()`（或 `connectOverCDP()`）来接管或维持一个长运行（Long-running）的浏览器实例，是自动化运维、AI Agent 浏览器工具 以及绕过反爬虫检测 的常见方案。然而，在长时间挂载或高并发的实际生产中，这种机制存在一系列底层设计与网络通信上的**稳定性陷阱（Reliability Pitfalls）**。 [](https://www.youtube.com/watch?v=vT19Uri0ntw)

1. 握手崩溃与连接假死（Handshake Stalls & Hanging） 

- **连接协商超时（CDP Drop Mid-Handshake）**：在网络抖动、CPU 瞬间高负载（如部署在 AWS Lambda 或高密度 Docker 容器内）时，Playwright 的 Node/Python WebSocket 在执行 CDP 会话握手协商时，常因为接收到无序或畸形的事件流而直接崩溃、报错，或者导致 `connect_over_cdp` 发生永久性卡死（Hanging）。
- **未捕获的后台运行环异常（Event Loop Closed）**：长运行脚本退出或重启时，如果异步事件循环（Event Loop）在垃圾回收（Garbage Collection）前被强制关闭，Playwright 内部负责维持 CDP 连接的后台任务（如 `Connection.run()`）会抛出未捕获的挂起异常（Task pending）。 [](https://github.com/microsoft/playwright-python/issues/2924)


2. 长时间空闲后的 Websocket 断开（Idle Disconnection） 

- **心跳丢失（Keep-Alive Failure）**：长运行的浏览器（通常挂载超过 12 小时以上）如果没有持续的页面交互，中间的网络网关、负载均衡器或操作系统自身的 TCP 栈会主动断开处于静默状态的 WebSocket。
- **连接假活（Ghost Connection）**：当远程浏览器崩溃、网络断开或被目标网站内存占满拉稀时，Playwright 端有时无法在第一时间感知到 CDP 断开。代码会继续执行命令，直到触发 30000ms+ 的全局动作超时（Timeout Exceeded）。 [](https://github.com/microsoft/playwright/issues/24252)


undefined

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



[#](#)[](/setprefs?sig=0_8N2gc83npYKEgZQVtM1wsVpVmCU%3D&source=en_ignored_notification&prev=https://www.google.com/search?q%3DPlaywright%2Bconnect_over_cdp%2BCDP%2Blong-running%2Bbrowser%2Bconnection%2Breliability%2Bpitfalls%2B2025%26udm%3D50%26sei%3Dut4Oaq_jEfzm2roP5frFOA&hl=en&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8QhoQCKAF6BAgGEC8)  
[](#) [1][2][3][4][5][7][8][9]


[](/preferences?lang=1&hl=zh-HK&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8QiIQCKAN6BAgGEDE#languages) [6]

---

## Sources:

[1] 全部 — https://www.google.com/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&sei=ut4Oaq_jEfzm2roP5frFOA&mstk=AUtExfDQ8b22IjxGNv-OFQMXECOUIfwnf6bG2zzlW3K8b4_EzYqqdd4VTBMPhQdVslut53mIdjOOy6A3sUV5T0F6Qd9zOziRKkJ-f6NMkWSWUpahjZUf6wi4hsynwiRBExlnStVij-1ohu8dVRLKhRF9-x22Q2W3FrPzRqg&csuir=1/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8Q0pQJegQIBhAF
[2] 圖片 — https://www.google.com/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&sei=ut4Oaq_jEfzm2roP5frFOA&mstk=AUtExfDQ8b22IjxGNv-OFQMXECOUIfwnf6bG2zzlW3K8b4_EzYqqdd4VTBMPhQdVslut53mIdjOOy6A3sUV5T0F6Qd9zOziRKkJ-f6NMkWSWUpahjZUf6wi4hsynwiRBExlnStVij-1ohu8dVRLKhRF9-x22Q2W3FrPzRqg&csuir=1/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&udm=2&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8Q0pQJegQIBhAH
[3] 影片 — https://www.google.com/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&sei=ut4Oaq_jEfzm2roP5frFOA&mstk=AUtExfDQ8b22IjxGNv-OFQMXECOUIfwnf6bG2zzlW3K8b4_EzYqqdd4VTBMPhQdVslut53mIdjOOy6A3sUV5T0F6Qd9zOziRKkJ-f6NMkWSWUpahjZUf6wi4hsynwiRBExlnStVij-1ohu8dVRLKhRF9-x22Q2W3FrPzRqg&csuir=1/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&udm=7&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8Q0pQJegQIBhAJ
[4] 新聞 — https://www.google.com/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&sei=ut4Oaq_jEfzm2roP5frFOA&mstk=AUtExfDQ8b22IjxGNv-OFQMXECOUIfwnf6bG2zzlW3K8b4_EzYqqdd4VTBMPhQdVslut53mIdjOOy6A3sUV5T0F6Qd9zOziRKkJ-f6NMkWSWUpahjZUf6wi4hsynwiRBExlnStVij-1ohu8dVRLKhRF9-x22Q2W3FrPzRqg&csuir=1/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&tbm=nws&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8Q0pQJegQIBhAL
[5] 購物 — https://www.google.com/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&sei=ut4Oaq_jEfzm2roP5frFOA&mstk=AUtExfDQ8b22IjxGNv-OFQMXECOUIfwnf6bG2zzlW3K8b4_EzYqqdd4VTBMPhQdVslut53mIdjOOy6A3sUV5T0F6Qd9zOziRKkJ-f6NMkWSWUpahjZUf6wi4hsynwiRBExlnStVij-1ohu8dVRLKhRF9-x22Q2W3FrPzRqg&csuir=1/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&udm=28&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[6] 地圖 — https://maps.google.com/maps?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&um=1&ie=UTF-8&ved=1t:200715&ictx=111
[7] 書籍 — https://www.google.com/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&udm=50&sei=ut4Oaq_jEfzm2roP5frFOA&mstk=AUtExfDQ8b22IjxGNv-OFQMXECOUIfwnf6bG2zzlW3K8b4_EzYqqdd4VTBMPhQdVslut53mIdjOOy6A3sUV5T0F6Qd9zOziRKkJ-f6NMkWSWUpahjZUf6wi4hsynwiRBExlnStVij-1ohu8dVRLKhRF9-x22Q2W3FrPzRqg&csuir=1/search?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&udm=36&prmd=ivns&source=lnms&sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8Q0pQJegQIBhAU
[8] 航班 — https://www.google.com/travel/flights?q=Playwright+connect_over_cdp+CDP+long-running+browser+connection+reliability+pitfalls+2025&sca_esv=d539714fd0df0db7&tbm=flm&prmd=ivns&source=lnms&ved=1t:200715&ictx=111
[9] 財經 — https://www.google.com/finance?sa=X&ved=2ahUKEwio_c2wlsqUAxX5ulYBHfeCCl8Q0pQJegQIBhAY
[10] 我的 Google 搜尋記錄 — https://myactivity.google.com/myactivity?product=83&utm_source=aim&utm_campaign=aim_tm