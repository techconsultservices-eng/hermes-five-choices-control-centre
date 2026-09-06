from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from installer import propagate_account


class AccountPropagationTests(unittest.TestCase):
    def test_authorized_account_is_copied_and_verified_without_outputting_secret(self):
        with tempfile.TemporaryDirectory(prefix="h5-auth-") as temp:
            home = Path(temp)
            assistant = home / "profiles" / "assistant"
            assistant.mkdir(parents=True)
            secret = "fake-oauth-token-for-test-only"
            (assistant / "auth.json").write_text(json.dumps({"token": secret}), encoding="utf-8")

            def fake_run(command, profile_home, *args):
                if args == ("config", "get", "model.provider"):
                    return "nous"
                if args == ("config", "get", "model.default"):
                    return "approved/test-model"
                if args[:2] == ("auth", "status"):
                    return "nous: logged in"
                return "ok"

            stdout = io.StringIO()
            with (
                mock.patch.object(propagate_account, "run", side_effect=fake_run),
                mock.patch.object(sys, "argv", [
                    "propagate_account.py", "--command", "hermes",
                    "--hermes-home", str(home),
                ]),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(propagate_account.main(), 0)

            output = stdout.getvalue()
            self.assertNotIn(secret, output)
            for profile in propagate_account.SPECIALISTS:
                copied = home / "profiles" / profile / "auth.json"
                self.assertEqual(copied.read_text(encoding="utf-8"), json.dumps({"token": secret}))


if __name__ == "__main__":
    unittest.main()
