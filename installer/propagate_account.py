#!/usr/bin/env python
"""Propagate one user-authorized Hermes OAuth account without reading its secrets."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

SPECIALISTS = ("pcfix", "donsetch-tinyfish", "image-creator", "teach-me", "grill-me")


def run(command: str, home: Path, *args: str) -> str:
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)
    result = subprocess.run([command, *args], env=env, capture_output=True, text=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError((result.stdout + "\n" + result.stderr).strip()[-800:])
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    args = parser.parse_args()
    assistant = args.hermes_home / "profiles" / "assistant"
    auth = assistant / "auth.json"
    if not auth.is_file():
        raise RuntimeError("Assistant OAuth setup did not create auth.json")
    provider = run(args.command, assistant, "config", "get", "model.provider").splitlines()[-1].strip()
    model = run(args.command, assistant, "config", "get", "model.default").splitlines()[-1].strip()
    if not provider or not model:
        raise RuntimeError("Assistant provider/model setup is incomplete")
    verified = []
    for profile in SPECIALISTS:
        home = args.hermes_home / "profiles" / profile
        home.mkdir(parents=True, exist_ok=True)
        shutil.copy2(auth, home / "auth.json")
        run(args.command, home, "config", "set", "model.provider", provider)
        run(args.command, home, "config", "set", "model.default", model)
        status = run(args.command, home, "auth", "status", provider)
        if "logged in" not in status.lower() and "authenticated" not in status.lower():
            raise RuntimeError(f"Account verification failed for {profile}: {status[-300:]}")
        verified.append(profile)
    print(json.dumps({"ok": True, "provider": provider, "model": model, "profiles": verified}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
