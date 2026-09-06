#!/usr/bin/env python
"""Build the unsigned second-laptop test installer using Windows built-ins."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
BUILD = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "Temp" / "H5IExpressBuild"
DIST_ZIP = PROJECT / "dist" / "hermes-five-choices-dashboard-0.1.0.zip"
TARGET = PROJECT / "dist" / "Hermes-Five-Choices-Test-Installer-0.1.0.exe"
TEMP_TARGET = BUILD / "H5Installer.exe"


def main() -> int:
    if not DIST_ZIP.is_file():
        raise FileNotFoundError("Build the dashboard package first")
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    for name in ("install_payload.ps1", "install_payload.vbs"):
        shutil.copy2(ROOT / name, BUILD / name)
    shutil.copy2(DIST_ZIP, BUILD / "payload.zip")
    source = str(BUILD).replace("/", "\\")
    target = str(TEMP_TARGET).replace("/", "\\")
    sed = f'''[Version]\nClass=IEXPRESS\nSEDVersion=3\n[Options]\nPackagePurpose=InstallApp\nShowInstallProgramWindow=1\nHideExtractAnimation=1\nUseLongFileName=1\nInsideCompressed=0\nCAB_FixedSize=0\nCAB_ResvCodeSigning=0\nRebootMode=N\nInstallPrompt=%InstallPrompt%\nDisplayLicense=%DisplayLicense%\nFinishMessage=%FinishMessage%\nTargetName=%TargetName%\nFriendlyName=%FriendlyName%\nAppLaunched=%AppLaunched%\nPostInstallCmd=%PostInstallCmd%\nAdminQuietInstCmd=%AdminQuietInstCmd%\nUserQuietInstCmd=%UserQuietInstCmd%\nSourceFiles=SourceFiles\n[Strings]\nInstallPrompt=\nDisplayLicense=\nFinishMessage=\nTargetName={target}\nFriendlyName=Hermes Five Choices Test Installer\nAppLaunched=wscript.exe //nologo install_payload.vbs\nPostInstallCmd=<None>\nAdminQuietInstCmd=\nUserQuietInstCmd=\nFILE0=\"install_payload.vbs\"\nFILE1=\"install_payload.ps1\"\nFILE2=\"payload.zip\"\n[SourceFiles]\nSourceFiles0={source}\\\n[SourceFiles0]\n%FILE0%=\n%FILE1%=\n%FILE2%=\n'''
    sed_path = BUILD / "installer.sed"
    sed_path.write_text(sed, encoding="ascii", newline="\r\n")
    iexpress = Path(r"C:\Windows\SysWOW64\iexpress.exe")
    if not iexpress.is_file():
        iexpress = Path(r"C:\Windows\System32\iexpress.exe")
    result = subprocess.run([str(iexpress), "/N", "/Q", str(sed_path)], capture_output=True, text=True, timeout=600, check=False)
    if result.returncode != 0 or not TEMP_TARGET.is_file():
        raise RuntimeError(f"IExpress failed ({result.returncode}): {result.stdout} {result.stderr}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMP_TARGET, TARGET)
    print(f"Test installer: {TARGET}")
    print(f"Size: {TARGET.stat().st_size} bytes")
    print("Signing: NOT SIGNED — suitable only for controlled second-laptop testing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
