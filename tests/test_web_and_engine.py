"""Integration tests for AutomationEngine safety guards and Web/Mobile Companion HTTP/SSE server."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
import urllib.error
import urllib.request

from poe_automate.automation import AutomationEngine
from poe_automate.config import ConfigManager
from poe_automate.library import LibraryManager
from poe_automate.web_server import WebCompanionServer


SAMPLE_ITEM = """Item Class: Body Armours
Rarity: Rare
Storm Carapace
Astral Plate
--------
Sockets: R-R-R-G-B-W
--------
Item Level: 85
--------
+12% to all Elemental Resistances (implicit)
--------
+105 to maximum Life
+42% to Fire Resistance"""


class TestWebCompanionAndEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg_path = os.path.join(self._tmp.name, "config.json")
        self.config = ConfigManager(self.cfg_path)
        self.library = LibraryManager()
        self.engine = AutomationEngine(self.config)
        self.server = WebCompanionServer(self.config, self.engine, self.library)
        ok = self.server.start(port=0, allow_lan=False)
        self.assertTrue(ok)
        self.base_url = self.server.get_urls()["local"]

    def tearDown(self) -> None:
        self.server.stop()
        self.engine.shutdown()
        self._tmp.cleanup()

    def _req(self, path: str, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def test_static_assets_and_path_traversal_blocked(self) -> None:
        with urllib.request.urlopen(self.base_url + "/", timeout=5) as resp:
            html = resp.read().decode("utf-8")
            self.assertEqual(resp.status, 200)
            self.assertIn("PoE AutoMate", html)
            self.assertIn("viewport", html)

        with urllib.request.urlopen(self.base_url + "/style.css", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("@media", resp.read().decode("utf-8"))

        with urllib.request.urlopen(self.base_url + "/app.js", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("EventSource", resp.read().decode("utf-8"))

        # Path traversal attempt must never succeed
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self.base_url + "/../main.py", timeout=5)
        self.assertIn(ctx.exception.code, (403, 404))

    def test_full_rest_api_flow_and_item_tester(self) -> None:
        code, state = self._req("/api/state")
        self.assertEqual(code, 200)
        self.assertTrue(state["ok"])
        self.assertIn("Flask", state["categories"])

        # Add filter via API
        code, added = self._req("/api/filters", "POST", {"name": "+# to maximum Life", "value": "95"})
        self.assertEqual(code, 201)
        self.assertEqual(len(added["config"]["filters"]), 1)

        # Test item via API -> should MATCH
        code, test_res = self._req("/api/test-item", "POST", {"text": SAMPLE_ITEM})
        self.assertEqual(code, 200)
        self.assertTrue(test_res["result"]["matched"])
        self.assertEqual(test_res["result"]["status"], "FOUND")

        # Toggle filter off -> should report NO_FILTERS
        code, toggled = self._req("/api/filters/0/toggle", "POST")
        self.assertEqual(code, 200)
        self.assertFalse(toggled["filter"]["active"])

        code, test_res2 = self._req("/api/test-item", "POST", {"text": SAMPLE_ITEM})
        self.assertEqual(code, 200)
        self.assertEqual(test_res2["result"]["status"], "NO_FILTERS")

        # Switch to color mode & test sockets (3R 1G 1B + 1W wildcard -> matches 4R 1G 1B!)
        code, _ = self._req(
            "/api/settings",
            "POST",
            {"search_mode": "color", "color_targets": {"R": 4, "G": 1, "B": 1, "W": 0}, "white_as_wildcard": True},
        )
        self.assertEqual(code, 200)
        code, color_res = self._req("/api/test-item", "POST", {"text": SAMPLE_ITEM})
        self.assertTrue(color_res["result"]["matched"])

        # Library search endpoint
        code, lib_res = self._req("/api/library?category=Flask&q=movement")
        self.assertEqual(code, 200)
        self.assertGreater(lib_res["total"], 0)

        # Delete filter
        code, del_res = self._req("/api/filters/0", "DELETE")
        self.assertEqual(code, 200)
        self.assertEqual(len(del_res["config"]["filters"]), 0)

    def test_sse_stream_delivers_init_event(self) -> None:
        req = urllib.request.Request(self.base_url + "/api/events")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))
            first_line = resp.readline().decode("utf-8").strip()
            second_line = resp.readline().decode("utf-8").strip()
            self.assertEqual(first_line, "event: init")
            self.assertTrue(second_line.startswith("data: "))
            payload = json.loads(second_line[len("data: ") :])
            self.assertIn("state", payload)
            self.assertIn("config", payload)

    def test_log_ring_buffer_is_bounded(self) -> None:
        for i in range(700):
            self.engine.log(f"msg {i}")
        logs = self.engine.get_logs(limit=0)
        self.assertLessEqual(len(logs), self.engine.MAX_LOG_ENTRIES)
        self.assertEqual(logs[-1]["text"], "msg 699")


class TestAutomationEngineSafety(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.config = ConfigManager(os.path.join(self._tmp.name, "config.json"))
        self.config.update({"sound_enabled": False, "click_delay": 0.05, "clipboard_delay": 0.03})
        self.engine = AutomationEngine(self.config)

    def tearDown(self) -> None:
        self.engine.shutdown()
        self._tmp.cleanup()

    def test_prestart_stops_when_already_matching(self) -> None:
        self.config.add_filter("+# to maximum Life", "100")
        self.engine.is_poe_active = lambda: True  # type: ignore[method-assign]
        self.engine.read_clipboard_after_copy = lambda delay=None: SAMPLE_ITEM  # type: ignore[method-assign]
        started = self.engine.start()
        self.assertFalse(started)
        self.assertEqual(self.engine.status, "FOUND")

    def test_auto_loop_releases_shift_and_stops_on_match(self) -> None:
        self.config.add_filter("+# to maximum Life", "100")
        rolls = [
            "Item Class: Body Armours\nRarity: Rare\nTest\n--------\nItem Level: 85\n--------\n+20 to maximum Life",
            "Item Class: Body Armours\nRarity: Rare\nTest\n--------\nItem Level: 85\n--------\n+40 to maximum Life",
            SAMPLE_ITEM,
        ]
        idx = {"i": 0}
        shift_events: list[str] = []

        def fake_read(delay=None):
            val = rolls[min(idx["i"], len(rolls) - 1)]
            idx["i"] += 1
            return val

        self.engine.is_poe_active = lambda: True  # type: ignore[method-assign]
        self.engine.read_clipboard_after_copy = fake_read  # type: ignore[method-assign]
        self.engine._perform_click = lambda: None  # type: ignore[method-assign]
        self.engine._hold_shift = lambda: shift_events.append("down")  # type: ignore[method-assign]
        self.engine._release_shift = lambda: shift_events.append("up")  # type: ignore[method-assign]

        started = self.engine.start()
        self.assertTrue(started)
        assert self.engine._worker is not None
        self.engine._worker.join(timeout=3.0)

        self.assertEqual(self.engine.status, "FOUND")
        self.assertEqual(self.engine.get_state()["attempts"], 2)
        self.assertIn("down", shift_events)
        self.assertIn("up", shift_events)
        self.assertEqual(shift_events[-1], "up")

    def test_auto_loop_separate_empty_and_same_counters(self) -> None:
        self.config.add_filter("+# to maximum Life", "999")
        same_item = "Item Class: Body Armours\nRarity: Rare\nTest\n--------\nItem Level: 85\n--------\n+10 to maximum Life"
        rolls = [same_item, "", "", same_item, "", "", ""]
        idx = {"i": 0}
        clicks = {"n": 0}

        def fake_read(delay=None):
            val = rolls[min(idx["i"], len(rolls) - 1)]
            idx["i"] += 1
            return val

        self.engine.is_poe_active = lambda: True  # type: ignore[method-assign]
        self.engine.read_clipboard_after_copy = fake_read  # type: ignore[method-assign]
        self.engine._perform_click = lambda: clicks.__setitem__("n", clicks["n"] + 1)  # type: ignore[method-assign]
        self.engine._hold_shift = lambda: None  # type: ignore[method-assign]
        self.engine._release_shift = lambda: None  # type: ignore[method-assign]

        started = self.engine.start()
        self.assertTrue(started)
        assert self.engine._worker is not None
        self.engine._worker.join(timeout=3.0)

        self.assertEqual(self.engine.status, "STOPPED")
        # Empty reads triggered retries without burning extra clicks
        self.assertEqual(self.engine.get_state()["attempts"], clicks["n"])


if __name__ == "__main__":
    unittest.main()
