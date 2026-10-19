# 第37～42课共用教学 HTTP API 规格

实现交给课程工程制作。使用 Python 3.8.9 及3.13均支持的标准库：`http.server.ThreadingHTTPServer`、`BaseHTTPRequestHandler`、`urllib.parse`、`json`、`threading`、`datetime`、`pathlib`。无需pip依赖。启动脚本默认 `127.0.0.1:8765`，手机课堂用显式参数 `--host 0.0.0.0`，启动时列出电脑局域网地址与说明。仅限隔离教学局域网，不对公网开放，无生产账号、TLS或权限系统。

所有响应含正确的 `Content-Length`，JSON为UTF-8，`ensure_ascii=False`；错误也为JSON对象。正文最大8192字节，超出413。未知方法405，未知路径404。数据变更以锁保护，保存到脚本旁独立 `teaching-data.json`，写临时文件后原子替换；读写失败返回500，不假报成功。API不记录真实姓名、手机号、位置、声音或图片。昵称为教学化名。

手机访问 `http://教师电脑IPv4:8765`。`127.0.0.1`仅表示当前设备本身。操作系统防火墙需允许此教学服务的专用网络访问。使用服务所在电脑浏览器先验证；无需互联网。浏览器跨源调试可以返回`Access-Control-Allow-Origin:*`及正确OPTIONS，仅用于本地示范，不依赖cookie。

## 数据与端点

| 方法与路径 | 状态与格式 | 精确行为 |
|---|---|---|
| GET `/api/v1/hello` | 200 `text/plain; charset=utf-8` | `你好，欢迎来到羽轩创意编程课堂！` |
| GET `/api/v1/info` | 200 JSON | 见下方默认对象 |
| GET `/api/v1/info?empty=1` | 200 JSON | 保留className，announcements和activities均为空列表 |
| GET `/api/v1/places?q=关键词` | 200 JSON | `{"items":[地点对象],"count":整数}`。trim、忽略英文大小写、name包含匹配；缺少或空q返回400 `{"error":"请输入地点关键词"}` |
| POST `/api/v1/feedback` | 201 JSON | Content-Type为`application/x-www-form-urlencoded`；字段kind,message。返回`{"id":"F0001","received":true}`，编号为持久化递增且不复用 |
| GET `/api/v1/messages` | 200 JSON | `{"items":[留言对象],"count":整数}`；id升序，最多最近50条 |
| POST `/api/v1/messages` | 201 JSON | 表单字段nick,message。返回`{"id":1,"received":true}`；成功持久化后才返回 |
| GET `/api/v1/missing` | 404 JSON | `{"error":"路径不存在"}` |

默认info：

```json
{"className":"创意班","announcements":[{"id":1,"title":"欢迎来到创意班","body":"今天用程序表达一个想法"},{"id":2,"title":"作品分享","body":"带上一条测试证据"}],"activities":["同伴试玩","创意改编","作品分享"],"updatedAt":"2026-10-18T09:00:00+08:00"}
```

updatedAt是服务示例数据修改时间，可以固定为随包示例值；客户端的缓存接收时间另行本地保存，不混淆。不得冒充实时公告来源。

地点表：

```json
[{"name":"图书角","floor":2,"note":"课间可借阅"},{"name":"创客教室","floor":3,"note":"在教师陪同下使用"},{"name":"运动器材室","floor":1,"note":"午休后开放"}]
```

feedback校验：kind只能为建议、问题、表扬；message trim后1～200字符。messages校验：nick trim后1～12字符，message trim后1～120字符；超长或空值400，错误JSON含`error`可读文字。教材不要求账号鉴权；不应称为可直接上线的安全留言平台。

留言对象：`{"id":1,"nick":"星星","message":"我的第一个APP完成啦","createdAt":"ISO8601含时区"}`。最多保留最近50条，计数和下个id持久化。未发布成功不清空客户端草稿。

## 受控故障测试

GET端点可加`delay_ms`（0～10000整数，超过范围400）在响应前延迟；如 `/api/v1/hello?delay_ms=6000` 对照客户端5000ms超时。可加`status=500`受控返回500 JSON错误；info还可加`invalid_json=1`返回200文本`{broken`检验解析错误。仅教学GET支持故障开关，POST不支持，以免模糊“超时是否已经写入”的真实语义。

为让AIA普通“刷新”按钮也能触发同样测试，启动脚本另支持`--scenario normal|delay|error|empty|invalid-json`（默认normal）：delay让GET延迟6000ms；error让GET返回500；empty只让info返回空公告/活动；invalid-json只让info返回坏JSON。教师切换启动场景后使用相同AIA操作即可，不要求修改积木或给主机框塞路径。终端清楚显示当前教学场景。客户端超时关闭连接导致服务写回BrokenPipe/ConnectionReset时，服务端仅记录已断开，不让处理线程堆栈污染课堂输出。发布版默认正常场景，故障模式仅用于可重复验证。

客户端同一时刻只允许一个请求，等待期间禁用冲突按钮，GotText/TimedOut/ErrorOccurred所有出口恢复状态。POST超时不自动重发，文字提示“结果未确认，请先检查后再重试”。Web.JsonTextDecodeWithDictionaries用于对象；不得使用旧JSON解码再假设返回字典。

## 实现验收

标准库`unittest`或等价实际HTTP脚本验证：UTF-8欢迎语；info空表；中文及空格查询编码；POST201和400；空昵称；正文超过上限；文件持久化恢复；两个客户端共享同一id；50条限制；延迟和500可复现。真实服务与AIA完整工程共同联调，不能只给接口文档或用浏览器前端冒充手机运行。

官方参考：

- https://ai2.appinventor.mit.edu/reference/components/connectivity.html#Web
- https://docs.python.org/3/library/http.server.html
- https://docs.python.org/3/library/urllib.parse.html
