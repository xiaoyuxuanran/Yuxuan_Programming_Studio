import concurrent.futures
import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.parse import urlencode
from teaching_server import TeachingServer


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.file = Path(self.temp.name) / "data.json"
        self.start()

    def start(self):
        self.server = TeachingServer(("127.0.0.1", 0), self.file, quiet=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def tearDown(self):
        self.stop()
        self.temp.cleanup()

    def request(self, method, path, fields=None, raw=None):
        body = raw if raw is not None else (urlencode(fields).encode() if fields is not None else None)
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=12)
        try:
            conn.request(method, path, body, {"Content-Type": "application/x-www-form-urlencoded"})
            response = conn.getresponse()
            data = response.read()
            self.assertEqual(int(response.getheader("Content-Length")), len(data))
            self.assertEqual(response.getheader("Access-Control-Allow-Origin"), "*")
            text = data.decode("utf-8")
            try:
                value = json.loads(text)
            except ValueError:
                value = text
            return response.status, value
        finally:
            conn.close()

    def test_utf8_info_query_and_errors(self):
        self.assertEqual(self.request("GET", "/api/v1/hello"), (200, "你好，欢迎来到羽轩创意编程课堂！"))
        self.assertEqual(self.request("GET", "/api/v1/info")[1]["className"], "创意班")
        empty = self.request("GET", "/api/v1/info?empty=1")[1]
        self.assertEqual(empty["announcements"], [])
        self.assertEqual(empty["activities"], [])
        self.assertEqual(self.request("GET", "/api/v1/places?" + urlencode({"q": " 图书 "}))[1]["items"][0]["floor"], 2)
        self.assertEqual(self.request("GET", "/api/v1/places?q=")[0], 400)
        self.assertEqual(self.request("GET", "/api/v1/places?q=none")[1]["count"], 0)
        self.assertEqual(self.request("GET", "/api/v1/missing")[0], 404)
        self.assertEqual(self.request("PUT", "/api/v1/info")[0], 405)
        self.assertEqual(self.request("OTHER", "/api/v1/info")[0], 405)
        self.assertEqual(self.request("POST", "/api/v1/info", {})[0], 405)

    def test_validation_and_body_limit(self):
        self.assertEqual(self.request("POST", "/api/v1/feedback", {"kind": "建议", "message": "支持分享"}), (201, {"id": "F0001", "received": True}))
        self.assertEqual(self.request("POST", "/api/v1/feedback", {"kind": "其他", "message": "好"})[0], 400)
        self.assertEqual(self.request("POST", "/api/v1/messages", {"nick": " ", "message": "好"})[0], 400)
        self.assertEqual(self.request("POST", "/api/v1/messages", {"nick": "星", "message": "a" * 121})[0], 400)
        self.assertEqual(self.request("POST", "/api/v1/feedback", raw=b"x=" + b"a" * 8193)[0], 413)
        self.assertEqual(self.server.store.data["nextMessageId"], 1)

    def test_concurrent_clients_and_persistence(self):
        def post(number):
            return self.request("POST", "/api/v1/messages", {"nick": "星星", "message": str(number)})
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            responses = list(pool.map(post, range(55)))
        self.assertTrue(all(code == 201 for code, value in responses))
        self.assertEqual(sorted(value["id"] for code, value in responses), list(range(1, 56)))
        messages = self.request("GET", "/api/v1/messages")[1]
        self.assertEqual(messages["count"], 50)
        self.assertEqual([x["id"] for x in messages["items"]], list(range(6, 56)))
        self.stop()
        self.start()
        self.assertEqual(self.request("GET", "/api/v1/messages")[1], messages)
        self.assertEqual(post(56)[1]["id"], 56)
        self.assertEqual(self.request("POST", "/api/v1/feedback", {"kind": "问题", "message": "试试"})[1]["id"], "F0001")

    def test_failed_write_does_not_commit(self):
        original = self.server.store._save
        def fail(data):
            raise OSError("controlled write failure")
        self.server.store._save = fail
        self.assertEqual(self.request("POST", "/api/v1/messages", {"nick": "星星", "message": "草稿"})[0], 500)
        self.assertEqual(self.server.store.data["messages"], [])
        self.server.store._save = original
        self.assertEqual(self.request("POST", "/api/v1/messages", {"nick": "星星", "message": "恢复"})[1]["id"], 1)

    def test_controlled_failures(self):
        start = time.monotonic()
        self.assertEqual(self.request("GET", "/api/v1/hello?delay_ms=120")[0], 200)
        self.assertGreaterEqual(time.monotonic() - start, 0.10)
        self.assertEqual(self.request("GET", "/api/v1/hello?delay_ms=-1")[0], 400)
        self.assertEqual(self.request("GET", "/api/v1/hello?delay_ms=10001")[0], 400)
        self.assertEqual(self.request("GET", "/api/v1/hello?status=500")[0], 500)
        self.assertEqual(self.request("GET", "/api/v1/info?invalid_json=1"), (200, "{broken"))
        self.server.scenario = "empty"
        self.assertEqual(self.request("GET", "/api/v1/info")[1]["activities"], [])
        self.server.scenario = "error"
        self.assertEqual(self.request("GET", "/api/v1/hello")[0], 500)
        self.server.scenario = "invalid-json"
        self.assertEqual(self.request("GET", "/api/v1/info")[1], "{broken")


if __name__ == "__main__":
    unittest.main(verbosity=2)
