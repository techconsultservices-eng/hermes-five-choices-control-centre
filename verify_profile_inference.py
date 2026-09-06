#!/usr/bin/env python
"""Harmless live inference probe for all Hermes Five Choices routes."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import dashboard_server as dashboard

OUTPUT = Path(__file__).resolve().parent / "verification" / "profile-inference-results.json"
PROMPT = "Five Choices release health check only. Reply exactly READY and nothing else."


def probe(profile: str) -> dict[str, object]:
    started = time.monotonic()
    payload = json.dumps({"model": profile, "messages": [{"role": "user", "content": PROMPT}], "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        f"{dashboard.HERMES_API}/p/{profile}/v1/chat/completions",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {dashboard.load_api_key(profile)}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            body = json.loads(response.read().decode("utf-8"))
            status = response.status
        content = str((((body.get("choices") or [{}])[0].get("message") or {}).get("content") or "")).strip()
        return {"profile": profile, "ok": status == 200 and content == "READY", "http_status": status, "elapsed_seconds": round(time.monotonic() - started, 2), "response_preview": content[:200]}
    except urllib.error.HTTPError as exc:
        return {"profile": profile, "ok": False, "http_status": exc.code, "elapsed_seconds": round(time.monotonic() - started, 2), "error": exc.read().decode("utf-8", errors="replace")[:300]}
    except Exception as exc:
        return {"profile": profile, "ok": False, "http_status": None, "elapsed_seconds": round(time.monotonic() - started, 2), "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    profiles = list(dashboard.ALLOWED_PROFILES)
    results: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(probe, profile): profile for profile in profiles}
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            print(f"{row['profile']}: {'OK' if row['ok'] else 'FAIL'} ({row['elapsed_seconds']}s)", flush=True)
    order = {profile: index for index, profile in enumerate(profiles)}
    results.sort(key=lambda row: order[str(row["profile"])])
    record = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api": dashboard.HERMES_API,
        "prompt": PROMPT,
        "total": len(results),
        "passed": sum(bool(row["ok"]) for row in results),
        "failed": sum(not bool(row["ok"]) for row in results),
        "results": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"SUMMARY {record['passed']}/{record['total']} passed; {record['failed']} failed")
    return 0 if record["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
