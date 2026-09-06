from __future__ import annotations

import os
import unittest
import json
from pathlib import Path
from unittest.mock import patch

import dashboard_server as dashboard

ROOT = Path(__file__).resolve().parents[1]


class DashboardServerTests(unittest.TestCase):
    def test_exact_six_profile_allowlist(self):
        self.assertEqual(
            list(dashboard.ALLOWED_PROFILES),
            ["assistant", "pcfix", "donsetch-tinyfish", "image-creator", "teach-me", "grill-me"],
        )

    def test_chat_validation_accepts_each_route(self):
        for profile in dashboard.ALLOWED_PROFILES:
            dashboard.validate_chat(profile, "hello", "resume", "test-channel")

    def test_chat_validation_rejects_unknown_profile(self):
        with self.assertRaisesRegex(ValueError, "not connected"):
            dashboard.validate_chat("marketing-brand", "hello", "resume", "test")

    def test_channel_rejects_path_or_space_characters(self):
        for value in ("../bad", "bad channel", "-bad"):
            with self.assertRaises(ValueError):
                dashboard.validate_chat("assistant", "hello", "resume", value)

    def test_active_profile_home_variable_does_not_change_machine_root(self):
        self.assertNotEqual(str(dashboard.HERMES_HOME), os.environ.get("HERMES_HOME", ""))
        self.assertTrue(str(dashboard.HERMES_HOME).replace("\\", "/").endswith("AppData/Local/hermes"))

    def test_static_root_is_product_owned(self):
        self.assertEqual(dashboard.STATIC_ROOT, ROOT / "web")

    def test_new_sessions_receive_unique_titles(self):
        titles = []

        class Response:
            def __init__(self, session_id):
                self.session_id = session_id
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return False
            def read(self):
                return json.dumps({"session": {"id": self.session_id}}).encode()

        def fake_request(_profile, _path, *, method, payload):
            self.assertEqual(method, "POST")
            titles.append(payload["title"])
            return Response(f"session-{len(titles)}")

        with (
            patch.dict(dashboard.SESSION_IDS, {}, clear=True),
            patch.object(dashboard, "api_request", side_effect=fake_request),
            patch.object(dashboard, "persist_session_index"),
            patch.object(dashboard.time, "time_ns", side_effect=[101, 102]),
        ):
            dashboard.ensure_session("assistant", "new", "smoke")
            dashboard.ensure_session("assistant", "new", "smoke")
        self.assertEqual(len(set(titles)), 2)
        self.assertTrue(all("Assistant · smoke" in title for title in titles))


class StaticProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

    def test_navigation_has_dashboard_five_choices_and_system(self):
        for page in ("dashboard", "tech", "web", "image", "teach", "grill", "system"):
            self.assertIn(f'data-page="{page}"', self.html)

    def test_five_resizable_workspaces_are_declared(self):
        self.assertIn("['tech','web','image','teach','grill']", self.js)
        self.assertIn("role=\"separator\"", self.js)
        self.assertIn("ArrowLeft", self.js)
        self.assertIn("ArrowRight", self.js)

    def test_no_private_thought_claim(self):
        self.assertNotIn("chain-of-thought", self.html.lower())
        self.assertNotIn("private thoughts", self.html.lower())

    def test_profile_keys_are_not_in_static_assets(self):
        combined = self.html + self.js + self.css
        self.assertNotIn("API_SERVER_KEY", combined)
        self.assertNotRegex(combined, r"sk-[A-Za-z0-9_-]{12,}")

    def test_no_mobile_acceptance_layout(self):
        self.assertIn("body{min-width:800px}", self.css)


if __name__ == "__main__":
    unittest.main()
