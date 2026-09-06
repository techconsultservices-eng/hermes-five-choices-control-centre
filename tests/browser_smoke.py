#!/usr/bin/env python
"""Real Edge/CDP smoke test for the Hermes Five Choices dashboard."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

EDGE = Path(r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
PORT = 9444
URL = os.environ.get("H5_TEST_BASE_URL", "http://127.0.0.1:9335/").rstrip("/") + "/"
EXPECTED_CONNECTED = int(os.environ.get("H5_EXPECT_CONNECTED", "6"))
TARGET_HOST = URL.split("://", 1)[1].rstrip("/")


def wait_json(url: str, seconds: int = 20):
    end = time.time() + seconds
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {url}")


def main() -> int:
    if not EDGE.is_file():
        raise FileNotFoundError(EDGE)
    user_data = Path(tempfile.mkdtemp(prefix="h5-edge-"))
    process = subprocess.Popen([
        str(EDGE), "--headless=new", f"--remote-debugging-port={PORT}",
        "--remote-allow-origins=*", f"--user-data-dir={user_data}",
        "--window-size=1440,900", "--no-first-run", "--disable-default-apps", URL,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_json(f"http://127.0.0.1:{PORT}/json/version")
        tabs = wait_json(f"http://127.0.0.1:{PORT}/json")
        end = time.time() + 20
        tab = None
        while time.time() < end:
            tabs = wait_json(f"http://127.0.0.1:{PORT}/json")
            tab = next((item for item in tabs if item.get("type") == "page" and TARGET_HOST in item.get("url", "")), None)
            if tab:
                break
            time.sleep(0.2)
        if not tab:
            raise RuntimeError(f"Edge did not expose the Five Choices page target: {tabs}")
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)
        counter = 0

        def command(method: str, params: dict | None = None):
            nonlocal counter
            counter += 1
            ws.send(json.dumps({"id": counter, "method": method, "params": params or {}}))
            while True:
                message = json.loads(ws.recv())
                if message.get("id") == counter:
                    if "error" in message:
                        raise RuntimeError(message["error"])
                    return message.get("result", {})

        def evaluate(expression: str):
            result = command("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
            return (result.get("result") or {}).get("value")

        command("Runtime.enable")
        end = time.time() + 20
        while time.time() < end:
            ready = evaluate("({ready:document.readyState,title:document.title,href:location.href})")
            if ready.get("ready") == "complete" and ready.get("title") == "Hermes Five Choices" and TARGET_HOST in ready.get("href", ""):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError(f"Dashboard document did not become ready: {ready}")

        structure_expression = """(() => ({
          title: document.title,
          choices: document.querySelectorAll('.choice-card').length,
          nav: document.querySelectorAll('.nav-item').length,
          resizers: document.querySelectorAll('.resizer').length,
          connected: [...document.querySelectorAll('[data-profile-state]')].filter(x=>x.textContent==='Connected').length,
          active: document.querySelector('.page.active')?.id,
          overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
        }))()"""
        end = time.time() + 20
        while time.time() < end:
            structure = evaluate(structure_expression)
            if structure.get("connected") == EXPECTED_CONNECTED:
                break
            time.sleep(0.2)
        assert structure == {"title": "Hermes Five Choices", "choices": 5, "nav": 7, "resizers": 5, "connected": EXPECTED_CONNECTED, "active": "page-dashboard", "overflow": False}, structure

        route_results = {}
        for page in ("tech", "web", "image", "teach", "grill", "system", "dashboard"):
            route_results[page] = evaluate(f"document.querySelector('.nav-item[data-page=\"{page}\"]').click(); location.hash + '|' + document.querySelector('.page.active').id")
            assert route_results[page] == f"#{page}|page-{page}", route_results

        split = evaluate("""(() => {
          const h=document.querySelector('[data-resizer="tech"]');
          h.focus();h.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
          return {saved:JSON.parse(localStorage.getItem('hermes-five-choices-v1')).splits.tech,role:h.getAttribute('role')};
        })()""")
        assert split["role"] == "separator" and split["saved"].endswith("%"), split

        theme = evaluate("document.querySelector('[data-theme-choice=\"plum\"]').click(); document.documentElement.dataset.theme")
        assert theme == "plum", theme
        persisted = evaluate("JSON.parse(localStorage.getItem('hermes-five-choices-v1')).theme")
        assert persisted == "plum", persisted

        print("EDGE_SMOKE_OK", json.dumps({"structure": structure, "routes": route_results, "split": split, "theme": persisted}))
        ws.close()
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(user_data, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
