"""羽轩 App Inventor 第37–42课教学接口。Python 3.8+，无第三方依赖。"""
import argparse
import copy
import json
import os
from pathlib import Path
import socket
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

INFO = {"className": "创意班", "announcements": [
    {"id": 1, "title": "欢迎来到创意班", "body": "今天用程序表达一个想法"},
    {"id": 2, "title": "作品分享", "body": "带上一条测试证据"}],
    "activities": ["同伴试玩", "创意改编", "作品分享"],
    "updatedAt": "2026-10-18T09:00:00+08:00"}
PLACES = [{"name": "图书角", "floor": 2, "note": "课间可借阅"},
          {"name": "创客教室", "floor": 3, "note": "在教师陪同下使用"},
          {"name": "运动器材室", "floor": 1, "note": "午休后开放"}]
GET_PATHS = {"/api/v1/hello", "/api/v1/info", "/api/v1/places", "/api/v1/messages"}
POST_PATHS = {"/api/v1/feedback", "/api/v1/messages"}


class DataStore:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.data = {"nextMessageId": 1, "nextFeedbackId": 1, "messages": [], "feedback": []}
        if self.path.exists():
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            for key in self.data:
                if key not in saved:
                    raise ValueError("教学数据缺少字段：" + key)
            if not isinstance(saved["messages"], list) or not isinstance(saved["feedback"], list):
                raise ValueError("教学数据列表损坏，请备份后检查数据文件")
            if not isinstance(saved["nextMessageId"], int) or not isinstance(saved["nextFeedbackId"], int):
                raise ValueError("教学数据编号损坏")
            self.data = saved

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(self.path))

    def append(self, kind, fields):
        with self.lock:
            candidate = copy.deepcopy(self.data)
            counter = "nextMessageId" if kind == "messages" else "nextFeedbackId"
            number = candidate[counter]
            identifier = number if kind == "messages" else "F%04d" % number
            record = dict(fields, id=identifier, createdAt=datetime.now(timezone.utc).astimezone().isoformat())
            candidate[kind].append(record)
            if kind == "messages":
                candidate[kind] = candidate[kind][-50:]
            candidate[counter] = number + 1
            self._save(candidate)
            self.data = candidate
            return identifier

    def messages(self):
        with self.lock:
            return copy.deepcopy(self.data["messages"][-50:])


class TeachingServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, data_path, scenario="normal", quiet=False):
        self.store = DataStore(data_path)
        self.scenario = scenario
        self.quiet = quiet
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "YuxuanTeaching/1.0"

    def __getattr__(self, name):
        if name.startswith("do_"):
            return self.unsupported
        raise AttributeError(name)

    def log_message(self, fmt, *args):
        if not self.server.quiet:
            print("%s %s" % (self.address_string(), fmt % args), flush=True)

    def send_data(self, status, value, text=False):
        raw = (value if text else json.dumps(value, ensure_ascii=False)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8" if text else "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            if self.command != "HEAD":
                self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.log_message("客户端已断开，响应不再写入")

    def error(self, status, text):
        self.send_data(status, {"error": text})

    def do_OPTIONS(self):
        self.send_data(204, "", text=True)

    def do_GET(self):
        parts = urlsplit(self.path)
        path, query = parts.path, parse_qs(parts.query, keep_blank_values=True)
        if path not in GET_PATHS:
            return self.error(405 if path in POST_PATHS else 404, "方法不允许" if path in POST_PATHS else "路径不存在")
        try:
            raw_delay = query.get("delay_ms", ["6000" if self.server.scenario == "delay" else "0"])[0]
            if not raw_delay.isdigit() or not 0 <= int(raw_delay) <= 10000:
                return self.error(400, "delay_ms须为0～10000的整数")
            if int(raw_delay):
                time.sleep(int(raw_delay) / 1000)
            if query.get("status", [""])[0] == "500" or self.server.scenario == "error":
                return self.error(500, "教学场景：服务暂时不可用")
            if path == "/api/v1/hello":
                return self.send_data(200, "你好，欢迎来到羽轩创意编程课堂！", text=True)
            if path == "/api/v1/info":
                if query.get("invalid_json", [""])[0] == "1" or self.server.scenario == "invalid-json":
                    return self.send_data(200, "{broken", text=True)
                data = copy.deepcopy(INFO)
                if query.get("empty", [""])[0] == "1" or self.server.scenario == "empty":
                    data.update(announcements=[], activities=[])
                return self.send_data(200, data)
            if path == "/api/v1/places":
                term = query.get("q", [""])[0].strip().casefold()
                if not term:
                    return self.error(400, "请输入地点关键词")
                items = [p for p in PLACES if term in p["name"].casefold()]
                return self.send_data(200, {"items": items, "count": len(items)})
            items = self.server.store.messages()
            return self.send_data(200, {"items": items, "count": len(items)})
        except (OSError, ValueError) as exc:
            self.log_message("数据读取失败：%s", type(exc).__name__)
            return self.error(500, "教学数据读取失败，请检查服务端终端")

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in POST_PATHS:
            return self.error(405 if path in GET_PATHS else 404, "方法不允许" if path in GET_PATHS else "路径不存在")
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            return self.error(415, "请使用表单编码application/x-www-form-urlencoded")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.error(400, "正文长度无效")
        if length > 8192:
            return self.error(413, "正文超过8192字节")
        if length < 0:
            return self.error(400, "正文长度无效")
        try:
            self.connection.settimeout(10)
            body = self.rfile.read(length).decode("utf-8", errors="strict")
            fields = parse_qs(body, keep_blank_values=True, encoding="utf-8", errors="strict", max_num_fields=12)
        except (ValueError, UnicodeError, OSError):
            return self.error(400, "表单编码无效或读取超时")
        get = lambda key: fields.get(key, [""])[0].strip()
        message = get("message")
        if path == "/api/v1/feedback":
            kind = get("kind")
            if kind not in ("建议", "问题", "表扬") or not 1 <= len(message) <= 200:
                return self.error(400, "请选择建议、问题或表扬，并输入1～200字内容")
            category, record = "feedback", {"kind": kind, "message": message}
        else:
            nick = get("nick")
            if not 1 <= len(nick) <= 12 or not 1 <= len(message) <= 120:
                return self.error(400, "昵称须为1～12字，留言须为1～120字")
            category, record = "messages", {"nick": nick, "message": message}
        try:
            identifier = self.server.store.append(category, record)
        except (OSError, ValueError) as exc:
            self.log_message("数据保存失败：%s", type(exc).__name__)
            return self.error(500, "保存失败，内容未确认写入；请检查服务端")
        return self.send_data(201, {"id": identifier, "received": True})

    def unsupported(self):
        return self.error(405, "方法不允许")

    do_PUT = do_DELETE = do_PATCH = do_HEAD = do_TRACE = do_CONNECT = unsupported


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("teaching-data.json"))
    parser.add_argument("--scenario", choices=["normal", "delay", "error", "empty", "invalid-json"], default="normal")
    args = parser.parse_args()
    server = TeachingServer((args.host, args.port), args.data, args.scenario)
    print("羽轩教学API | 场景：%s | 数据：%s" % (args.scenario, args.data.resolve()))
    print("电脑自测：http://127.0.0.1:%s/api/v1/hello" % args.port)
    if args.host == "0.0.0.0":
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
        for address in addresses:
            print("手机同一局域网尝试：http://%s:%s（选择实际网卡IPv4）" % (address, args.port))
        print("专用教学局域网使用。防火墙允许专用网络；勿映射公网。手机127.0.0.1不是教师电脑。")
    else:
        print("仅本机访问；手机课堂请加参数 --host 0.0.0.0，并确认同一局域网。")
    print("Ctrl+C停止。默认normal；故障场景只用于教学测试。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
