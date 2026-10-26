import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


script = Path(__file__).parents[1] / "overrides/cyk-iterm-settings/scripts/picker_server.py"
spec = importlib.util.spec_from_file_location("picker_server", script)
picker = importlib.util.module_from_spec(spec)
previous = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    spec.loader.exec_module(picker)
finally:
    sys.dont_write_bytecode = previous


class PickerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / 'project "<&>'
        self.target.mkdir()
        self.target = self.target.resolve()
        self.session = Path(self.temp.name) / "session"
        self.server, self.meta = picker.create_server(self.target, "1c1c1c", self.session)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def post(self, data, origin=None):
        origin = origin or "http://" + self.server.address
        request = Request(self.meta["url"] + "choice", data=json.dumps(data).encode(), headers={"Origin": origin, "Content-Type": "application/json"})
        return urlopen(request, timeout=3)

    def test_initial_color_is_not_a_decision_and_page_is_escaped(self):
        self.assertFalse((self.session / "choice.json").exists())
        with urlopen(self.meta["url"], timeout=3) as response:
            page = response.read().decode()
        self.assertIn("&lt;&amp;&gt;", page)
        self.assertIn("\\u003c", page)
        self.assertNotIn("__TARGET_", page)
        self.assertNotIn('claude.use', page)

    def test_decision_is_validated_and_bound_to_this_session(self):
        with self.post({"path": str(self.target), "hex": "0f1f2a", "luminance": 9999}):
            pass
        choice = json.loads((self.session / "choice.json").read_text())
        self.assertEqual(choice["path"], str(self.target))
        self.assertEqual(choice["session"], self.meta["session"])
        self.assertEqual(choice["hex"], "0f1f2a")
        self.assertLess(choice["luminance"], 80)

    def test_invalid_target_or_color_never_creates_choice(self):
        for data in [{"path": "/wrong", "hex": "0f1f2a"}, {"path": str(self.target), "hex": "invalid"}]:
            with self.assertRaises(HTTPError) as error:
                self.post(data)
            self.assertEqual(error.exception.code, 400)
        self.assertFalse((self.session / "choice.json").exists())

    def test_other_origin_and_unknown_token_are_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.post({"path": str(self.target), "hex": "0f1f2a"}, "http://other.example")
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            urlopen("http://" + self.server.address + "/unknown/", timeout=3)
        self.assertEqual(error.exception.code, 404)
        self.assertFalse((self.session / "choice.json").exists())

    def test_old_session_directory_cannot_be_reused(self):
        with self.assertRaises(FileExistsError):
            picker.create_server(self.target, "1c1c1c", self.session)


if __name__ == "__main__":
    unittest.main()
