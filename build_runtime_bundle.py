#!/usr/bin/env python
"""Build the credential-free frozen Windows runtime for Hermes Five Choices."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "runtime-build" / "source"
PYTHON_ROOT = Path(os.environ.get(
    "H5_PYTHON_ROOT",
    r"C:\Users\DAC\AppData\Roaming\uv\python\cpython-3.11.15-windows-x86_64-none",
))
WHEELHOUSE = ROOT / "runtime-build" / "wheelhouse"
REQUIREMENTS = ROOT / "runtime-build" / "requirements-win64.txt"
OUT_DIR = ROOT / "runtime-build" / "dist"
OUT = OUT_DIR / "hermes-five-choices-runtime-0.20.6-win64.zip"
MANIFEST_OUT = ROOT / "runtime-build" / "runtime-manifest.json"
SBOM_OUT = ROOT / "runtime-build" / "runtime-sbom.cdx.json"
EXPECTED_COMMIT = "26350357d76e4508c8df9304a3374bdc5a6f6220"
EXPECTED_TREE = "e5eaa11e762b0920e92f5a4d2c1a773d17718efe"
EXPECTED_PYTHON = "3.11.15"
FIXED_TIME = (2026, 8, 29, 0, 0, 0)
FORBIDDEN_EXACT = {
    ".env", "auth.json", "state.db", "MEMORY.md", "USER.md",
    "gateway_state.json", "dashboard_sessions.json",
}
FORBIDDEN_PARTS = {"sessions", "logs", "cache", "receipts", "outputs"}


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(args)}\n{result.stdout[-1000:]}{result.stderr[-1000:]}")
    return result.stdout.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_info(name: str, mode: int = 0o644) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name.replace("\\", "/"), FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def add_bytes(zf: zipfile.ZipFile, name: str, data: bytes, records: dict[str, dict]) -> None:
    zf.writestr(zip_info(name), data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    records[name] = {"sha256": sha256_bytes(data), "size": len(data)}


def assert_safe(name: str) -> None:
    path = Path(name)
    if path.name in FORBIDDEN_EXACT or any(part.lower() in FORBIDDEN_PARTS for part in path.parts):
        raise RuntimeError(f"Forbidden live state in runtime bundle: {name}")


def tracked_source_files() -> list[str]:
    commit = run("git", "rev-parse", "HEAD", cwd=SOURCE)
    tree = run("git", "rev-parse", "HEAD^{tree}", cwd=SOURCE)
    dirty = run("git", "status", "--porcelain", cwd=SOURCE)
    if commit != EXPECTED_COMMIT or tree != EXPECTED_TREE or dirty:
        raise RuntimeError(f"Source identity mismatch: commit={commit}, tree={tree}, dirty={bool(dirty)}")
    raw = run("git", "ls-files", "-z", cwd=SOURCE)
    return [item for item in raw.split("\0") if item]


def parse_components(requirements: str) -> list[dict]:
    components: dict[tuple[str, str], dict] = {}
    for raw in requirements.splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^ ;\\]+)", raw.strip())
        if not match:
            continue
        name, version = match.groups()
        key = (name.lower().replace("_", "-"), version)
        components[key] = {
            "type": "library", "name": name, "version": version,
            "purl": f"pkg:pypi/{key[0]}@{version}",
        }
    return [components[key] for key in sorted(components)]


def build() -> dict:
    python_exe = PYTHON_ROOT / "python.exe"
    if not python_exe.is_file():
        raise RuntimeError(f"Pinned Python is missing: {PYTHON_ROOT}")
    version = run(str(python_exe), "-c", "import platform;print(platform.python_version())")
    if version != EXPECTED_PYTHON:
        raise RuntimeError(f"Python mismatch: {version}")
    if not REQUIREMENTS.is_file():
        raise RuntimeError("Locked requirements export is missing")
    wheels = sorted(WHEELHOUSE.glob("*.whl"), key=lambda p: p.name.lower())
    if not wheels:
        raise RuntimeError("Offline wheelhouse is empty")

    requirements_text = REQUIREMENTS.read_text(encoding="utf-8")
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.5",
        "serialNumber": "urn:uuid:9fd853e7-7ec6-5ed5-a67a-19f5e8ddc156", "version": 1,
        "metadata": {
            "component": {"type": "application", "name": "Hermes Five Choices Frozen Runtime", "version": "0.20.6"},
            "properties": [
                {"name": "hermes.source.commit", "value": EXPECTED_COMMIT},
                {"name": "hermes.source.tree", "value": EXPECTED_TREE},
                {"name": "python.version", "value": EXPECTED_PYTHON},
            ],
        },
        "components": parse_components(requirements_text),
    }
    sbom_bytes = (json.dumps(sbom, indent=2, sort_keys=True) + "\n").encode()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict] = {}
    tracked = tracked_source_files()
    with zipfile.ZipFile(OUT, "w", allowZip64=True) as zf:
        for rel in tracked:
            assert_safe(rel)
            add_bytes(zf, f"runtime/hermes-agent/{rel}", (SOURCE / rel).read_bytes(), records)
        python_files = sorted(
            (p for p in PYTHON_ROOT.rglob("*") if p.is_file()),
            key=lambda p: p.relative_to(PYTHON_ROOT).as_posix().lower(),
        )
        for path in python_files:
            rel = path.relative_to(PYTHON_ROOT).as_posix()
            assert_safe(rel)
            add_bytes(zf, f"runtime/python/{rel}", path.read_bytes(), records)
        for wheel in wheels:
            assert_safe(wheel.name)
            add_bytes(zf, f"runtime/wheelhouse/{wheel.name}", wheel.read_bytes(), records)
        add_bytes(zf, "runtime/requirements-win64.txt", requirements_text.encode(), records)
        add_bytes(zf, "runtime/runtime-sbom.cdx.json", sbom_bytes, records)

        manifest = {
            "schema": 1, "product": "Hermes Five Choices", "runtime_version": "0.20.6",
            "source_commit": EXPECTED_COMMIT, "source_tree": EXPECTED_TREE,
            "python_version": EXPECTED_PYTHON, "platform": "windows-x86_64",
            "install_mode": "editable-source-offline-wheels",
            "extras": ["web", "mcp", "exa", "firecrawl", "parallel-web", "fal"],
            "files": records,
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        zf.writestr(zip_info("runtime/runtime-manifest.json"), manifest_bytes, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    manifest["bundle"] = {"path": str(OUT), "sha256": sha256_file(OUT), "size": OUT.stat().st_size}
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SBOM_OUT.write_bytes(sbom_bytes)
    return {
        "ok": True, "bundle": str(OUT), "sha256": manifest["bundle"]["sha256"],
        "size": manifest["bundle"]["size"], "files": len(records),
        "source_files": len(tracked), "python_files": len(python_files),
        "wheels": len(wheels), "components": len(sbom["components"]),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
