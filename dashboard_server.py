#!/usr/bin/env python
"""Loopback companion for Hermes Five Choices.

Serves the product-owned dashboard and proxies only six allowlisted profiles to
Hermes' authenticated API. Profile API keys remain server-side.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

HOST = os.environ.get("H5_HOST", "127.0.0.1")
PORT = int(os.environ.get("H5_PORT", "9335"))
PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = PROJECT_ROOT / "web"
DATA_ROOT = PROJECT_ROOT / "data"
HERMES_HOME = Path(os.environ.get("H5_HERMES_ROOT", str(Path.home() / "AppData/Local/hermes")))
HERMES_API = os.environ.get("HERMES_API", "http://127.0.0.1:8642").rstrip("/")
ALLOWED_PROFILES = {
    "assistant": "Assistant",
    "pcfix": "Tech Support",
    "donsetch-tinyfish": "Web Search & Scrape",
    "image-creator": "Image Creator",
    "teach-me": "Teach Me",
    "grill-me": "Grill Me",
}
SESSION_IDS: dict[str, str] = {}
STATE_FILE = DATA_ROOT / "dashboard_sessions.json"
SESSION_LOCK = threading.Lock()


def profile_root(profile: str) -> Path:
    return HERMES_HOME / "profiles" / profile


def profile_env(profile: str) -> Path:
    return profile_root(profile) / ".env"


def load_api_key(profile: str = "assistant") -> str:
    env_file = profile_env(profile)
    if not env_file.is_file():
        raise RuntimeError(f"Environment file is missing for profile '{profile}'")
    for raw in env_file.read_text(encoding="utf-8-sig").splitlines():
        if raw.startswith("API_SERVER_KEY="):
            key = raw.split("=", 1)[1].strip().strip("\"'")
            if len(key) >= 16:
                return key
    raise RuntimeError(f"API_SERVER_KEY is missing or too short for profile '{profile}'")


def load_session_index() -> dict[str, str]:
    try:
        value = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def persist_session_index() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    temp = STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(SESSION_IDS, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(STATE_FILE)


def validate_chat(profile: str, message: str, mode: str, channel: str) -> None:
    if profile not in ALLOWED_PROFILES:
        raise ValueError("Profile is not connected to Hermes Five Choices")
    if not message.strip():
        raise ValueError("Message cannot be empty")
    if len(message) > 20_000:
        raise ValueError("Message is too long")
    if mode not in {"new", "resume"}:
        raise ValueError("Mode must be new or resume")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", channel):
        raise ValueError("Invalid dashboard channel")


def profile_api_url(profile: str, path: str) -> str:
    return f"{HERMES_API}/p/{quote(profile, safe='')}{path}"


def api_request(profile: str, path: str, *, method: str = "GET", payload: dict | None = None, timeout: int = 30):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {load_api_key(profile)}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(profile_api_url(profile, path), data=body, headers=headers, method=method)
    return urlopen(request, timeout=timeout)


def ensure_session(profile: str, mode: str, channel: str) -> tuple[str, bool]:
    key = f"{profile}:{channel}"
    with SESSION_LOCK:
        if not SESSION_IDS:
            SESSION_IDS.update(load_session_index())
        if mode == "new":
            SESSION_IDS.pop(key, None)
        current = SESSION_IDS.get(key)
    if current:
        return current, True
    title = f"Five Choices · {ALLOWED_PROFILES[profile]} · {channel} · {time.time_ns()}"
    with api_request(profile, "/api/sessions", method="POST", payload={"title": title}) as response:
        data = json.loads(response.read().decode("utf-8"))
    session_id = str((data.get("session") or {}).get("id") or "").strip()
    if not session_id:
        raise RuntimeError("Hermes API did not return a session ID")
    with SESSION_LOCK:
        SESSION_IDS[key] = session_id
        persist_session_index()
    return session_id, False


def runtime_version() -> str:
    try:
        with api_request("assistant", "/health", timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data.get("version") or "unknown")
    except Exception:
        return "unknown"


def hermes_command() -> str:
    configured = os.environ.get("HERMES_COMMAND")
    if configured:
        return configured
    local = HERMES_HOME / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
    return str(local) if local.is_file() else "hermes"


class FiveChoicesHandler(SimpleHTTPRequestHandler):
    server_version = "HermesFiveChoices/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.client_address[0]} - {fmt % args}")

    def send_json(self, payload: dict[str, object], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        return not origin or origin in {f"http://{HOST}:{PORT}", f"http://localhost:{PORT}"}

    def read_json(self, max_bytes: int = 25_000) -> dict:
        if self.headers.get_content_type() != "application/json":
            raise TypeError("Content-Type must be application/json")
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > max_bytes:
            raise ValueError("Invalid request size")
        if length == 0:
            return {}
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            version = runtime_version()
            ok = version != "unknown"
            self.send_json({"ok": ok, "service": "hermes-five-choices", "runtime_version": version, "upstream": HERMES_API}, HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE)
            return
        if path == "/api/profiles":
            profiles = []
            for slug, name in ALLOWED_PROFILES.items():
                root = profile_root(slug)
                profiles.append({
                    "slug": slug,
                    "name": name,
                    "connected": (root / "config.yaml").is_file() and (root / "auth.json").is_file() and profile_env(slug).is_file(),
                    "session_id": next((value for key, value in SESSION_IDS.items() if key.startswith(f"{slug}:")), None),
                })
            self.send_json({"ok": True, "profiles": profiles, "count": len(profiles)})
            return
        if path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return
        super().do_GET()

    def stream_chat(self, profile: str, message: str, mode: str, channel: str) -> None:
        session_id, resumed = ensure_session(profile, mode, channel)
        path = f"/api/sessions/{quote(session_id, safe='')}/chat/stream"
        with api_request(profile, path, method="POST", payload={"message": message}, timeout=240) as upstream:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            meta = {"profile": profile, "display_name": ALLOWED_PROFILES[profile], "session_id": session_id, "resumed": resumed}
            self.wfile.write(f"event: dashboard.meta\ndata: {json.dumps(meta)}\n\n".encode("utf-8"))
            self.wfile.flush()
            while True:
                chunk = upstream.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if not self.origin_allowed():
            self.send_json({"ok": False, "error": "Origin is not allowed"}, HTTPStatus.FORBIDDEN)
            return
        try:
            payload = self.read_json()
            if path == "/api/system/open-desktop":
                desktop = ROOT / "desktop" / "Hermes.exe"
                if not desktop.is_file():
                    self.send_json({"ok": False, "error": "Hermes Desktop is not included; repair this installation"}, HTTPStatus.SERVICE_UNAVAILABLE)
                    return
                runtime_command = Path(hermes_command()).resolve()
                env = dict(os.environ)
                env.update({
                    "HERMES_HOME": str(HERMES_HOME),
                    "HERMES_DESKTOP_HERMES": str(runtime_command),
                    "HERMES_DESKTOP_USER_DATA_DIR": str(HERMES_HOME.parent / "desktop"),
                    "HERMES_DESKTOP_IGNORE_EXISTING": "0",
                })
                subprocess.Popen([str(desktop)], cwd=str(desktop.parent), env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                self.send_json({"ok": True, "action": "open-hermes-desktop"})
                return
            if path != "/api/chat/stream":
                self.send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            profile = str(payload.get("profile", ""))
            message = str(payload.get("message", ""))
            mode = str(payload.get("mode", "resume"))
            channel = str(payload.get("channel", "default"))
            validate_chat(profile, message, mode, channel)
            self.stream_chat(profile, message, mode, channel)
        except TypeError as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
                message = (detail.get("error") or {}).get("message") or str(detail)
            except Exception:
                message = str(exc)
            self.send_json({"ok": False, "error": f"Hermes API: {message}"}, HTTPStatus.BAD_GATEWAY)
        except (URLError, TimeoutError) as exc:
            self.send_json({"ok": False, "error": f"Hermes API unavailable: {exc}"}, HTTPStatus.BAD_GATEWAY)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_GATEWAY)


def main() -> None:
    load_api_key("assistant")
    print(f"Hermes Five Choices: http://{HOST}:{PORT}/")
    print(f"Streaming upstream: {HERMES_API} (profile keys held server-side)")
    ThreadingHTTPServer((HOST, PORT), FiveChoicesHandler).serve_forever()


if __name__ == "__main__":
    main()
