#!/usr/bin/env python
"""Start or stop the frozen Five Choices services safely."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

import psutil


def healthy(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def detached_flags() -> int:
    return (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


def spawn(args: list[str], *, cwd: Path, env: dict[str, str], log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    handle = log.open("ab")
    try:
        subprocess.Popen(
            args, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
            stdout=handle, stderr=subprocess.STDOUT, creationflags=detached_flags(),
            close_fds=True,
        )
    finally:
        handle.close()


def wait_for(url: str, seconds: int = 30) -> bool:
    end = time.time() + seconds
    while time.time() < end:
        if healthy(url):
            return True
        time.sleep(0.5)
    return False


def listener_records(port: int, role: str) -> list[dict]:
    records = []
    for connection in psutil.net_connections(kind="tcp"):
        if connection.status != psutil.CONN_LISTEN or not connection.laddr or connection.laddr.port != port or not connection.pid:
            continue
        try:
            process = psutil.Process(connection.pid)
            records.append({
                "role": role,
                "pid": process.pid,
                "created": process.create_time(),
                "cwd": process.cwd(),
                "port": port,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return records


def stop_recorded(pid_file: Path, allowed_roots: tuple[Path, ...]) -> dict:
    stopped: list[int] = []
    skipped: list[int] = []
    try:
        records = json.loads(pid_file.read_text(encoding="utf-8")) if pid_file.is_file() else []
    except (OSError, json.JSONDecodeError):
        records = []
    allowed = tuple(str(path.resolve()).lower() for path in allowed_roots)
    for record in records:
        pid = int(record.get("pid", 0))
        try:
            process = psutil.Process(pid)
            same_start = abs(process.create_time() - float(record.get("created", 0))) < 2
            cwd = process.cwd().lower()
            allowed_cwd = any(cwd.startswith(root) for root in allowed)
            if not same_start or not allowed_cwd:
                skipped.append(pid)
                continue
            children = process.children(recursive=True)
            for child in reversed(children):
                child.terminate()
            process.terminate()
            _, alive = psutil.wait_procs([*children, process], timeout=10)
            for survivor in alive:
                survivor.kill()
            stopped.append(pid)
        except psutil.NoSuchProcess:
            continue
        except (psutil.AccessDenied, ValueError):
            skipped.append(pid)
    pid_file.unlink(missing_ok=True)
    return {"ok": not skipped, "stopped": stopped, "skipped": skipped, "pid_file": str(pid_file)}


def main() -> int:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-root", type=Path, default=local / "HermesFiveChoices")
    parser.add_argument("--runtime-root", type=Path, default=local / "HermesFiveChoicesRuntime")
    parser.add_argument("--hermes-home", type=Path, default=local / "HermesFiveChoicesData" / "hermes")
    parser.add_argument("--gateway-port", type=int, default=8648)
    parser.add_argument("--dashboard-port", type=int, default=9335)
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()
    args.app_root = args.app_root.resolve()
    args.runtime_root = args.runtime_root.resolve()
    args.hermes_home = args.hermes_home.resolve()
    pid_file = args.hermes_home.parent / "run" / "services.json"

    if args.stop:
        result = stop_recorded(pid_file, (args.app_root, args.runtime_root, args.hermes_home))
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    python = args.runtime_root / "hermes-agent" / "venv" / "Scripts" / "python.exe"
    command = args.runtime_root / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
    dashboard = args.app_root / "dashboard_server.py"
    if not python.is_file() or not command.is_file() or not dashboard.is_file():
        raise RuntimeError("Hermes Five Choices installation is incomplete; run the installer to repair it")

    gateway_url = f"http://127.0.0.1:{args.gateway_port}/health"
    dashboard_url = f"http://127.0.0.1:{args.dashboard_port}/api/health"
    logs = args.hermes_home.parent / "logs"
    base_env = dict(os.environ)
    base_env["PYTHONIOENCODING"] = "utf-8"

    if not healthy(gateway_url):
        env = dict(base_env)
        env.update({
            "HERMES_HOME": str(args.hermes_home / "profiles" / "assistant"),
            "HERMES_GATEWAY_DETACHED": "1",
            "VIRTUAL_ENV": str(args.runtime_root / "hermes-agent" / "venv"),
            "PYTHONPATH": str(args.runtime_root / "hermes-agent"),
            "API_SERVER_PORT": str(args.gateway_port),
        })
        spawn(
            [str(python), "-u", "-m", "hermes_cli.main", "--profile", "assistant", "gateway", "run"],
            cwd=args.hermes_home / "profiles" / "assistant", env=env, log=logs / "gateway.log",
        )
    gateway_ok = wait_for(gateway_url)

    if gateway_ok and not healthy(dashboard_url):
        env = dict(base_env)
        env.update({
            "H5_HERMES_ROOT": str(args.hermes_home),
            "HERMES_API": f"http://127.0.0.1:{args.gateway_port}",
            "H5_PORT": str(args.dashboard_port),
            "HERMES_COMMAND": str(command),
        })
        spawn([str(python), "-u", str(dashboard)], cwd=args.app_root, env=env, log=logs / "dashboard.log")
    dashboard_ok = gateway_ok and wait_for(dashboard_url)

    records = listener_records(args.gateway_port, "gateway") + listener_records(args.dashboard_port, "dashboard")
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    result = {
        "ok": gateway_ok and dashboard_ok and bool(records),
        "gateway": {"url": gateway_url, "healthy": gateway_ok},
        "dashboard": {"url": dashboard_url, "healthy": dashboard_ok},
        "tracked_processes": len(records),
        "logs": str(logs),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
