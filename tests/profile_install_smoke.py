#!/usr/bin/env python
"""Install all six clean distributions into a fresh isolated Hermes home."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "profile-distributions"
HOME = ROOT / "verification" / "all-profiles-hermes-home"
REPORT = ROOT / "verification" / "profile-install-results.json"
EXPECTED = {
    "assistant": "Assistant",
    "pcfix": "Tech Support",
    "donsetch-tinyfish": "Web Search & Scrape",
    "image-creator": "Image Creator",
    "teach-me": "Teach Me",
    "grill-me": "Grill Me",
}
FORBIDDEN = {".env", "auth.json", "state.db", "state.db-wal", "state.db-shm", "projects.db"}


def read_display_name(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("display_name:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def main() -> int:
    shutil.rmtree(HOME, ignore_errors=True)
    HOME.mkdir(parents=True)
    env = os.environ.copy()
    env["HERMES_HOME"] = str(HOME)
    results = []
    for profile, expected_name in EXPECTED.items():
        target_name = f"h5-test-{profile}"
        command = [
            "hermes", "profile", "install", str(SOURCE / profile),
            "--name", target_name, "--force", "-y",
        ]
        run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120, check=False)
        target = HOME / "profiles" / target_name
        skills = list(target.rglob("SKILL.md")) if target.is_dir() else []
        forbidden = sorted(
            str(path.relative_to(target)).replace("\\", "/")
            for path in target.rglob("*")
            if path.is_file() and path.name in FORBIDDEN
        ) if target.is_dir() else []
        display_name = read_display_name(target / "profile.yaml") if (target / "profile.yaml").is_file() else ""
        ok = (
            run.returncode == 0
            and display_name == expected_name
            and len(skills) == 1
            and not forbidden
            and (target / "distribution.yaml").is_file()
            and (target / "SOUL.md").is_file()
        )
        results.append({
            "profile": profile,
            "installed_name": target_name,
            "ok": ok,
            "exit_code": run.returncode,
            "display_name": display_name,
            "skill_count": len(skills),
            "forbidden": forbidden,
            "error": run.stderr.strip()[:400] if run.returncode else "",
        })
        print(f"{profile}: {'OK' if ok else 'FAIL'} ({display_name}; skills={len(skills)})")
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": sum(1 for item in results if item["ok"]),
        "failed": sum(1 for item in results if not item["ok"]),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"SUMMARY {payload['passed']}/{payload['total']} passed")
    print(f"REPORT {REPORT}")
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
