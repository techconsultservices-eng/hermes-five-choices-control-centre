#!/usr/bin/env python
"""Transactional installer core for Hermes Five Choices.

Self-contained: provisions portable Python + Hermes source + wheels,
installs the product and creates isolated profiles with auto-generated API keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

PRODUCT_VERSION = "0.1.0"
REQUIRED_HERMES_VERSION = "0.20.6"
REQUIRED_HERMES_COMMIT = "26350357d76e4508c8df9304a3374bdc5a6f6220"
REQUIRED_HERMES_TREE = "e5eaa11e762b0920e92f5a4d2c1a773d17718efe"
RUNTIME_BUNDLE_NAME = "hermes-five-choices-runtime-0.20.6-win64.zip"
REQUIRED_RUNTIME_HASHES = {
    "uv.lock": "c7badb9d95bd177b0c80220f71799e3c1cb12118e4d9a5e7f37e843bebb8a1de",
    "pyproject.toml": "8fdd016886353ed18ad293c840a0422f0f750b64b30d1e19ad21649441b3f80b",
    "package-lock.json": "83beeba3f6e7826312444c7b64067488afae9ed88ad7326ecef61ac235bab86d",
}
PROFILES = ("assistant", "pcfix", "donsetch-tinyfish", "image-creator", "teach-me", "grill-me")
SPECIALISTS = tuple(name for name in PROFILES if name != "assistant")
PRODUCT_COPY_ITEMS = (
    "web", "desktop", "profile-distributions", "installer", ".gitignore", "dashboard_server.py", "run_companion.bat",
    "start_five_choices.bat", "start_background.bat", "PRODUCT_COMPATIBILITY_MANIFEST.yaml", "REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md",
    "release-manifest.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 300) -> str:
    result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        text = (result.stdout + "\n" + result.stderr).strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {args[0]} {args[1] if len(args) > 1 else ''}\n{text[-1200:]}")
    return result.stdout.strip()


def command_path(runtime_root: Path) -> str:
    candidates = [
        runtime_root / "hermes-agent" / "venv" / "Scripts" / "hermes.exe",
        runtime_root / "hermes-agent" / "venv" / "Scripts" / "hermes-script.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(f"Hermes command is missing under {runtime_root}")


def hermes_version(command: str) -> str:
    text = run_checked([command, "--version"], timeout=30)
    match = re.search(r"(?:Hermes Agent v?|hermes-agent\s+)(\d+\.\d+\.\d+)", text, re.I)
    if not match:
        match = re.search(r"\b(\d+\.\d+\.\d+)\b", text)
    if not match:
        raise RuntimeError(f"Unable to verify Hermes version: {text[:300]}")
    return match.group(1)


def runtime_evidence(command: str, runtime_root: Path, *, allow_provisional: bool = False) -> dict:
    version = hermes_version(command)
    runtime = runtime_root / "hermes-agent"
    errors: list[str] = []
    if version != REQUIRED_HERMES_VERSION:
        errors.append(f"version {version}, expected {REQUIRED_HERMES_VERSION}")
    hashes = {}
    for rel, expected in REQUIRED_RUNTIME_HASHES.items():
        path = runtime / rel
        actual = sha256(path) if path.is_file() else "missing"
        hashes[rel] = actual
        if actual != expected:
            errors.append(f"runtime hash mismatch {rel}")
    commit = ""
    tree = ""
    runtime_receipt = runtime / "runtime-receipt.json"
    if runtime_receipt.is_file():
        try:
            data = json.loads(runtime_receipt.read_text(encoding="utf-8"))
            commit = str(data.get("source_commit", ""))
            tree = str(data.get("source_tree", ""))
        except (OSError, json.JSONDecodeError):
            pass
    if commit != REQUIRED_HERMES_COMMIT or tree != REQUIRED_HERMES_TREE:
        errors.append("runtime source commit/receipt mismatch")
    if errors and not allow_provisional:
        raise RuntimeError("Unsupported runtime detected: " + "; ".join(errors))
    return {
        "version": version,
        "source_commit": commit,
        "source_tree": tree,
        "hashes": hashes,
        "provisional_override": bool(errors),
    }


def _safe_zip_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    for member in members:
        path = Path(member.filename)
        if path.is_absolute() or ".." in path.parts or not member.filename.startswith("runtime/"):
            raise RuntimeError(f"Unsafe runtime archive member: {member.filename}")
    return members


def verify_runtime_tree(runtime_root: Path) -> dict:
    manifest_path = runtime_root / "runtime-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("Runtime manifest is missing after extraction")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_commit") != REQUIRED_HERMES_COMMIT or manifest.get("source_tree") != REQUIRED_HERMES_TREE:
        raise RuntimeError("Runtime source identity does not match the approved release")
    errors = []
    for rel, record in manifest.get("files", {}).items():
        if not rel.startswith("runtime/"):
            errors.append(f"invalid runtime path {rel}")
            continue
        path = runtime_root / rel[len("runtime/"):]
        if not path.is_file():
            errors.append(f"missing {rel}")
        elif sha256(path) != record.get("sha256"):
            errors.append(f"hash mismatch {rel}")
    if errors:
        raise RuntimeError("Runtime verification failed: " + "; ".join(errors[:20]))
    return manifest


def _setup_portable_python(runtime_root: Path) -> Path:
    python = runtime_root / "python" / "python.exe"
    if not python.is_file():
        raise RuntimeError("Pinned standalone Python is missing")
    venv = runtime_root / "hermes-agent" / "venv"
    venv_python = venv / "Scripts" / "python.exe"
    if venv_python.is_file():
        return venv_python
    run_checked([str(python), "-m", "venv", str(venv)], timeout=180)
    if not venv_python.is_file():
        raise RuntimeError("Pinned Python did not create the private venv")
    return venv_python


def _install_hermes_in_venv(venv_python: Path, runtime_root: Path) -> Path:
    source_root = runtime_root / "hermes-agent"
    wheelhouse = runtime_root / "wheelhouse"
    requirements = runtime_root / "requirements-win64.txt"
    run_checked([str(venv_python), "-m", "pip", "install", "--no-index", "--find-links", str(wheelhouse), "--require-hashes", "-r", str(requirements)], timeout=600)
    run_checked([str(venv_python), "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation", "-e", str(source_root)], timeout=300)
    return source_root / "venv" / "Scripts" / "hermes.exe"


def provision_runtime(source: Path, runtime_root: Path, *, allow_provisional: bool = False) -> dict:
    bundle = source / "runtime" / RUNTIME_BUNDLE_NAME
    if not bundle.is_file():
        raise FileNotFoundError("The embedded runtime bundle is missing")
    staging_parent = runtime_root.with_name(runtime_root.name + ".staging-" + str(os.getpid()))
    rollback_root = runtime_root.with_name(runtime_root.name + ".rollback")
    shutil.rmtree(staging_parent, ignore_errors=True)
    shutil.rmtree(rollback_root, ignore_errors=True)
    staging_parent.mkdir(parents=True)
    try:
        with zipfile.ZipFile(bundle) as archive:
            _safe_zip_members(archive)
            archive.extractall(staging_parent)
        extracted = staging_parent / "runtime"
        manifest = verify_runtime_tree(extracted)
        shutil.rmtree(rollback_root, ignore_errors=True)
        if runtime_root.exists():
            runtime_root.replace(rollback_root)
        extracted.replace(runtime_root)
        venv_python = _setup_portable_python(runtime_root)
        command = _install_hermes_in_venv(venv_python, runtime_root)
        runtime_receipt = {
            "runtime_version": REQUIRED_HERMES_VERSION,
            "source_commit": REQUIRED_HERMES_COMMIT,
            "source_tree": REQUIRED_HERMES_TREE,
            "python_version": manifest.get("python_version"),
            "bundle_sha256": sha256(bundle),
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (runtime_root / "hermes-agent" / "runtime-receipt.json").write_text(
            json.dumps(runtime_receipt, indent=2) + "\n", encoding="utf-8"
        )
        evidence = runtime_evidence(command, runtime_root, allow_provisional=allow_provisional)
    except Exception:
        shutil.rmtree(runtime_root, ignore_errors=True)
        if rollback_root.exists():
            rollback_root.replace(runtime_root)
        shutil.rmtree(staging_parent, ignore_errors=True)
        raise
    shutil.rmtree(staging_parent, ignore_errors=True)
    return {"evidence": evidence, "rollback": str(rollback_root) if rollback_root.exists() else None}


def verify_source(source: Path) -> list[str]:
    missing = [item for item in PRODUCT_COPY_ITEMS if not (source / item).exists()]
    if missing:
        raise RuntimeError("Package is incomplete: " + ", ".join(missing))
    manifest_path = source / "release-manifest.json"
    if not manifest_path.is_file():
        return ["missing release-manifest.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for rel, expected in manifest.get("hashes", {}).items():
        path = source / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
        elif sha256(path) != expected:
            errors.append(f"hash mismatch {rel}")
    bundle = source / "runtime" / RUNTIME_BUNDLE_NAME
    if not bundle.is_file():
        errors.append(f"missing runtime/{RUNTIME_BUNDLE_NAME}")
    return errors


def profile_install(command: str, source: Path, hermes_home: Path, profile: str) -> None:
    env = dict(os.environ)
    env["HERMES_HOME"] = str(hermes_home)
    distribution = source / "profile-distributions" / profile
    run_checked(
        [command, "profile", "install", str(distribution), "--name", profile, "--force", "-y"],
        env=env, timeout=180,
    )


def update_env_key(path: Path, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else []
    replacement = f"{key}={value}"
    written = False
    updated = []
    for line in lines:
        if line.startswith(key + "="):
            if not written:
                updated.append(replacement)
                written = True
        else:
            updated.append(line)
    if not written:
        updated.append(replacement)
    path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def config_set(command: str, profile_home: Path, key: str, value: str) -> None:
    env = dict(os.environ)
    env["HERMES_HOME"] = str(profile_home)
    run_checked([command, "config", "set", key, value], env=env, timeout=60)


def configure_profiles(command: str, hermes_home: Path) -> dict:
    api_key = secrets.token_urlsafe(32)
    for profile in PROFILES:
        home = hermes_home / "profiles" / profile
        update_env_key(home / ".env", "API_SERVER_KEY", api_key)
    assistant_home = hermes_home / "profiles" / "assistant"
    config_set(command, assistant_home, "gateway.multiplex_profiles", "true")
    for profile in SPECIALISTS:
        config_set(command, hermes_home / "profiles" / profile, "gateway.platforms.api_server.enabled", "false")
    return {"api_key_generated": True, "multiplex_owner": "assistant", "secondary_listeners_disabled": list(SPECIALISTS)}


def receipt(target: Path, action: str, details: dict) -> Path:
    receipts = target / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    path = receipts / f"{int(time.time())}-{action}.json"
    record = {
        "product": "Hermes Five Choices", "version": PRODUCT_VERSION, "action": action,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **details,
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _copy_product(source: Path, target: Path) -> Path | None:
    rollback = target.with_name(target.name + ".rollback")
    shutil.rmtree(rollback, ignore_errors=True)
    if target.exists():
        target.replace(rollback)
    target.mkdir(parents=True)
    try:
        for item in PRODUCT_COPY_ITEMS:
            src = source / item
            dst = target / item
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        if rollback.exists():
            for name in ("data", "outputs", "receipts"):
                previous = rollback / name
                current = target / name
                if previous.exists() and not current.exists():
                    if previous.is_dir():
                        shutil.copytree(previous, current)
                    else:
                        shutil.copy2(previous, current)
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        if rollback.exists():
            rollback.replace(target)
        raise
    return rollback if rollback.exists() else None


def install(
    source: Path, target: Path, runtime_root: Path, hermes_home: Path, *,
    skip_profiles: bool = False, skip_runtime: bool = False, allow_provisional: bool = False,
) -> dict:
    errors = verify_source(source)
    if errors:
        raise RuntimeError("Source verification failed: " + "; ".join(errors))
    runtime_result: dict = {"skipped": True}
    if not skip_runtime:
        runtime_result = provision_runtime(source, runtime_root, allow_provisional=allow_provisional)
    command = command_path(runtime_root) if not (skip_runtime and skip_profiles) else ""
    if skip_runtime and not skip_profiles:
        runtime_result = {"evidence": runtime_evidence(command, runtime_root, allow_provisional=allow_provisional)}
    product_rollback = _copy_product(source, target)
    try:
        profile_config: dict = {"skipped": True}
        if not skip_profiles:
            for profile in PROFILES:
                profile_install(command, source, hermes_home, profile)
            profile_config = configure_profiles(command, hermes_home)
        path = receipt(target, "install", {
            "runtime": runtime_result,
            "profiles": [] if skip_profiles else list(PROFILES),
            "profile_config": profile_config,
            "source": str(source), "target": str(target),
            "runtime_root": str(runtime_root), "hermes_home": str(hermes_home),
            "product_rollback": str(product_rollback) if product_rollback else None,
        })
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        if product_rollback and product_rollback.exists():
            product_rollback.replace(target)
        raise
    return {
        "ok": True, "receipt": str(path), "target": str(target),
        "runtime_root": str(runtime_root), "hermes_home": str(hermes_home),
        "rollback": str(product_rollback) if product_rollback else None,
    }


def verify_install(
    target: Path, runtime_root: Path, hermes_home: Path, *,
    skip_runtime: bool = False, skip_profiles: bool = False,
) -> dict:
    missing = [item for item in PRODUCT_COPY_ITEMS if not (target / item).exists()]
    errors = [f"missing {item}" for item in missing]
    manifest_path = target / "release-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, expected in manifest.get("hashes", {}).items():
            if rel.startswith("runtime/"):
                continue
            path = target / rel
            if not path.is_file():
                errors.append(f"missing {rel}")
            elif sha256(path) != expected:
                errors.append(f"hash mismatch {rel}")
    runtime = {"skipped": True}
    if not skip_runtime:
        try:
            runtime = runtime_evidence(command_path(runtime_root), runtime_root)
        except Exception as exc:
            errors.append(str(exc))
    profiles = {name: (hermes_home / "profiles" / name).is_dir() for name in PROFILES}
    if not skip_profiles:
        for name, exists in profiles.items():
            if not exists:
                errors.append(f"missing profile {name}")
    return {"ok": not errors, "errors": errors, "runtime": runtime, "profiles": profiles, "target": str(target)}


def rollback(target: Path, runtime_root: Path) -> dict:
    saved = target.with_name(target.name + ".rollback")
    runtime_saved = runtime_root.with_name(runtime_root.name + ".rollback")
    if not saved.exists() and not runtime_saved.exists():
        raise RuntimeError("No rollback installation is available")
    failed = target.with_name(target.name + f".failed-{int(time.time())}")
    runtime_failed = runtime_root.with_name(runtime_root.name + f".failed-{int(time.time())}")
    if saved.exists():
        if target.exists():
            target.replace(failed)
        saved.replace(target)
    if runtime_saved.exists():
        if runtime_root.exists():
            runtime_root.replace(runtime_failed)
        runtime_saved.replace(runtime_root)
    path = receipt(target, "rollback", {
        "failed_install": str(failed) if failed.exists() else None,
        "failed_runtime": str(runtime_failed) if runtime_failed.exists() else None,
    })
    return {"ok": True, "receipt": str(path), "target": str(target), "runtime_root": str(runtime_root)}


def uninstall(target: Path, runtime_root: Path, hermes_home: Path, preserve_root: Path) -> dict:
    preserve_root.mkdir(parents=True, exist_ok=True)
    preserved = []
    if hermes_home.exists():
        preserved.append(str(hermes_home))
    product_roots = [target, target.with_name(target.name + ".rollback")]
    product_roots.extend(sorted(target.parent.glob(target.name + ".failed-*")))
    runtime_roots = [runtime_root, runtime_root.with_name(runtime_root.name + ".rollback")]
    runtime_roots.extend(sorted(runtime_root.parent.glob(runtime_root.name + ".failed-*")))
    for index, product_root in enumerate(product_roots):
        if not product_root.exists():
            continue
        destination_root = preserve_root / ("product" if index == 0 else f"recovery/{product_root.name}")
        for name in ("data", "outputs", "receipts"):
            src = product_root / name
            if src.exists():
                dst = destination_root / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
                shutil.move(str(src), str(dst))
                preserved.append(str(dst))
        shutil.rmtree(product_root, ignore_errors=False)
    for candidate in runtime_roots:
        if candidate.exists():
            shutil.rmtree(candidate, ignore_errors=False)
    residual = [str(path) for path in (*product_roots, *runtime_roots) if path.exists()]
    if residual:
        raise RuntimeError("Uninstall incomplete; paths remain: " + "; ".join(residual))
    record = preserve_root / f"uninstall-{int(time.time())}.json"
    record.write_text(json.dumps({
        "product": "Hermes Five Choices", "action": "uninstall", "preserved": preserved,
        "removed": [str(path) for path in (*product_roots, *runtime_roots)], "hermes_home_preserved": str(hermes_home),
    }, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "preserved": preserved, "receipt": str(record)}


def defaults() -> tuple[Path, Path, Path, Path]:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    return (
        local / "HermesFiveChoices",
        local / "HermesFiveChoicesRuntime",
        local / "HermesFiveChoicesData" / "hermes",
        local / "HermesFiveChoicesData",
    )


def build_parser() -> argparse.ArgumentParser:
    target, runtime_root, hermes_home, preserve_root = defaults()
    parser = argparse.ArgumentParser(description="Hermes Five Choices transactional bootstrapper")
    parser.add_argument("action", choices=("plan", "install", "verify", "rollback", "uninstall"))
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--target", type=Path, default=target)
    parser.add_argument("--runtime-root", type=Path, default=runtime_root)
    parser.add_argument("--hermes-home", type=Path, default=hermes_home)
    parser.add_argument("--preserve-root", type=Path, default=preserve_root)
    parser.add_argument("--skip-profiles", action="store_true", help="Test only: do not invoke profile install")
    parser.add_argument("--skip-runtime", action="store_true", help="Test only: do not provision runtime")
    parser.add_argument("--allow-provisional", action="store_true", help="Development only: allow non-approved runtime version")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source, target = args.source.resolve(), args.target.resolve()
    runtime_root, hermes_home = args.runtime_root.resolve(), args.hermes_home.resolve()
    if args.action == "plan":
        result = {
            "ok": True, "action": "plan", "source": str(source), "target": str(target),
            "runtime_root": str(runtime_root), "hermes_home": str(hermes_home),
            "profiles": list(PROFILES), "required_hermes": REQUIRED_HERMES_VERSION,
            "source_errors": verify_source(source),
        }
    elif args.action == "install":
        result = install(
            source, target, runtime_root, hermes_home,
            skip_profiles=args.skip_profiles, skip_runtime=args.skip_runtime,
            allow_provisional=args.allow_provisional,
        )
    elif args.action == "verify":
        result = verify_install(target, runtime_root, hermes_home, skip_runtime=args.skip_runtime, skip_profiles=args.skip_profiles)
    elif args.action == "rollback":
        result = rollback(target, runtime_root)
    else:
        result = uninstall(target, runtime_root, hermes_home, args.preserve_root.resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())