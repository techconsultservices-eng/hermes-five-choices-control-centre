from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from installer import bootstrapper

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "dist" / "hermes-five-choices-dashboard-0.1.0"


class BootstrapperTests(unittest.TestCase):
    def test_plan_source_is_complete_and_hashes_match(self):
        self.assertEqual(bootstrapper.verify_source(PACKAGE), [])

    def test_product_install_verify_rollback_and_preserving_uninstall(self):
        with tempfile.TemporaryDirectory(prefix="h5-bootstrap-") as temp:
            root = Path(temp)
            target = root / "install"
            runtime_root = root / "runtime"
            hermes_home = root / "data" / "hermes"
            preserve = root / "preserved"
            first = bootstrapper.install(
                PACKAGE, target, runtime_root, hermes_home,
                skip_profiles=True, skip_runtime=True,
            )
            self.assertTrue(first["ok"])
            self.assertTrue(bootstrapper.verify_install(
                target, runtime_root, hermes_home,
                skip_runtime=True, skip_profiles=True,
            )["ok"])
            marker = target / "data" / "customer.txt"
            marker.parent.mkdir()
            marker.write_text("keep me", encoding="utf-8")
            second = bootstrapper.install(
                PACKAGE, target, runtime_root, hermes_home,
                skip_profiles=True, skip_runtime=True,
            )
            self.assertTrue(second["ok"])
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep me")
            marker.write_text("new state", encoding="utf-8")
            restored = bootstrapper.rollback(target, runtime_root)
            self.assertTrue(restored["ok"])
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep me")
            removed = bootstrapper.uninstall(target, runtime_root, hermes_home, preserve)
            self.assertTrue(removed["ok"])
            self.assertFalse(target.exists())
            self.assertFalse(target.with_name(target.name + ".rollback").exists())
            self.assertFalse(any(target.parent.glob(target.name + ".failed-*")))
            self.assertEqual((preserve / "product" / "data" / "customer.txt").read_text(encoding="utf-8"), "keep me")
            recovered = list((preserve / "recovery").glob("*/data/customer.txt"))
            self.assertTrue(recovered)
            self.assertEqual(recovered[0].read_text(encoding="utf-8"), "new state")

    def test_missing_package_file_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="h5-incomplete-") as temp:
            root = Path(temp)
            with self.assertRaisesRegex(RuntimeError, "Package is incomplete"):
                bootstrapper.install(
                    root, root / "target", root / "runtime", root / "data",
                    skip_profiles=True, skip_runtime=True,
                )

    def test_exact_runtime_commit_tree_and_hash_are_required(self):
        with tempfile.TemporaryDirectory(prefix="h5-runtime-") as temp:
            runtime_root = Path(temp)
            runtime = runtime_root / "hermes-agent"
            runtime.mkdir(parents=True)
            lock = runtime / "uv.lock"
            lock.write_text("frozen", encoding="utf-8")
            (runtime / "runtime-receipt.json").write_text(json.dumps({
                "source_commit": bootstrapper.REQUIRED_HERMES_COMMIT,
                "source_tree": bootstrapper.REQUIRED_HERMES_TREE,
            }), encoding="utf-8")
            expected = bootstrapper.sha256(lock)
            with (
                mock.patch.object(bootstrapper, "REQUIRED_RUNTIME_HASHES", {"uv.lock": expected}),
                mock.patch.object(bootstrapper, "hermes_version", return_value=bootstrapper.REQUIRED_HERMES_VERSION),
            ):
                evidence = bootstrapper.runtime_evidence("hermes", runtime_root)
                self.assertFalse(evidence["provisional_override"])
                self.assertEqual(evidence["source_tree"], bootstrapper.REQUIRED_HERMES_TREE)
                lock.write_text("drifted", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "Unsupported runtime detected"):
                    bootstrapper.runtime_evidence("hermes", runtime_root)

    def test_profile_configuration_preserves_existing_env_and_disables_secondaries(self):
        with tempfile.TemporaryDirectory(prefix="h5-config-") as temp:
            home = Path(temp)
            for profile in bootstrapper.PROFILES:
                profile_home = home / "profiles" / profile
                profile_home.mkdir(parents=True)
                (profile_home / ".env").write_text("CUSTOM_PROVIDER_KEY=preserve-locally\n", encoding="utf-8")
            calls = []
            with (
                mock.patch.object(bootstrapper.secrets, "token_urlsafe", return_value="generated-local-api-key-123456789"),
                mock.patch.object(bootstrapper, "config_set", side_effect=lambda command, ph, key, value: calls.append((ph.name, key, value))),
            ):
                result = bootstrapper.configure_profiles("hermes", home)
            self.assertTrue(result["api_key_generated"])
            for profile in bootstrapper.PROFILES:
                text = (home / "profiles" / profile / ".env").read_text(encoding="utf-8")
                self.assertIn("CUSTOM_PROVIDER_KEY=preserve-locally", text)
                self.assertIn("API_SERVER_KEY=generated-local-api-key-123456789", text)
            self.assertIn(("assistant", "gateway.multiplex_profiles", "true"), calls)
            for profile in bootstrapper.SPECIALISTS:
                self.assertIn((profile, "gateway.platforms.api_server.enabled", "false"), calls)


if __name__ == "__main__":
    unittest.main()
