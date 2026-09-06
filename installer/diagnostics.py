#!/usr/bin/env python
"""Redacted post-install diagnostics for Hermes Five Choices."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from bootstrapper import PROFILES, SPECIALISTS, command_path, verify_install


def env_value(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def config_get(command: str, home: Path, key: str) -> str:
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)
    result = subprocess.run(
        [command, "config", "get", key], env=env, capture_output=True,
        text=True, timeout=30, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "missing"


def http_health(url: str) -> dict:
    try:
        with urlopen(url, timeout=4) as response:
            body = json.loads(response.read().decode("utf-8"))
        return {"reachable": True, "status": response.status, "ok": bool(body.get("ok", True))}
    except Exception as exc:
        return {"reachable": False, "error_type": type(exc).__name__}


def main() -> int:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=local / "HermesFiveChoices")
    parser.add_argument("--runtime-root", type=Path, default=local / "HermesFiveChoicesRuntime")
    parser.add_argument("--hermes-home", type=Path, default=local / "HermesFiveChoicesData" / "hermes")
    parser.add_argument("--check-services", action="store_true")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:8648/health")
    parser.add_argument("--dashboard-url", default="http://127.0.0.1:9335/api/health")
    args = parser.parse_args()

    result = verify_install(args.target, args.runtime_root, args.hermes_home)
    command = command_path(args.runtime_root)
    keys = {
        profile: env_value(args.hermes_home / "profiles" / profile / ".env", "API_SERVER_KEY")
        for profile in PROFILES
    }
    fingerprints = {hashlib.sha256(value.encode()).hexdigest() if value else "" for value in keys.values()}
    api_key_check = {
        "present_for_all_profiles": all(len(value) >= 16 for value in keys.values()),
        "same_local_key_for_all_profiles": len(fingerprints) == 1 and "" not in fingerprints,
        "values_redacted": True,
    }
    gateway_config = {
        "assistant_multiplex": config_get(
            command, args.hermes_home / "profiles" / "assistant", "gateway.multiplex_profiles"
        ),
        "secondary_api_listeners": {
            profile: config_get(
                command, args.hermes_home / "profiles" / profile,
                "gateway.platforms.api_server.enabled",
            )
            for profile in SPECIALISTS
        },
    }
    errors = list(result.get("errors", []))
    if not api_key_check["present_for_all_profiles"]:
        errors.append("API_SERVER_KEY is missing from one or more profiles")
    if not api_key_check["same_local_key_for_all_profiles"]:
        errors.append("Profile API keys do not match")
    if gateway_config["assistant_multiplex"].lower() != "true":
        errors.append("Assistant multiplex gateway is not enabled")
    for profile, value in gateway_config["secondary_api_listeners"].items():
        if value.lower() != "false":
            errors.append(f"Secondary API listener is not disabled: {profile}")
    services = {}
    if args.check_services:
        services = {
            "gateway": http_health(args.gateway_url),
            "dashboard": http_health(args.dashboard_url),
        }
        for name, health in services.items():
            if not health.get("reachable"):
                errors.append(f"{name} is not reachable")

    report = {
        "ok": not errors,
        "runtime": result.get("runtime"),
        "profiles": result.get("profiles"),
        "api_key": api_key_check,
        "gateway_config": gateway_config,
        "services": services,
        "errors": errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
