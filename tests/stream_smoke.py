#!/usr/bin/env python
"""Exercise a real streaming turn through the Five Choices companion."""
from __future__ import annotations

import json
import os
import urllib.request

BASE_URL = os.environ.get("H5_TEST_BASE_URL", "http://127.0.0.1:9335").rstrip("/")
URL = BASE_URL + "/api/chat/stream"
PAYLOAD = {"profile": "pcfix", "message": "Five Choices streaming check only. Reply exactly STREAM_READY and nothing else.", "mode": "new", "channel": "acceptance-stream"}


def main() -> int:
    request = urllib.request.Request(URL, data=json.dumps(PAYLOAD).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", "Origin": BASE_URL})
    with urllib.request.urlopen(request, timeout=240) as response:
        text = response.read().decode("utf-8")
        status = response.status
    events = []
    answer = ""
    for block in text.replace("\r\n", "\n").split("\n\n"):
        event = "message"
        data_lines = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        if not data_lines:
            continue
        data = json.loads("\n".join(data_lines))
        events.append(event)
        if event == "assistant.delta":
            answer += str(data.get("delta") or "")
        elif event == "assistant.completed":
            answer = str(data.get("content") or answer)
    required = {"dashboard.meta", "assistant.completed"}
    ok = status == 200 and answer.strip() == "STREAM_READY" and required.issubset(events)
    print(json.dumps({"ok": ok, "http_status": status, "events": events, "answer": answer.strip()}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
