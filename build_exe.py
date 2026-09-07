"""One-click Windows executable build and packaging script for ResearchGuard.
Compiles standalone Windows desktop application without requiring external Python runtime.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def kill_running_instances():
    """Terminates any running instances of ResearchGuard to prevent locked DLL errors."""
    try:
        subprocess.run(
            ["powershell", "-Command", "Get-Process ResearchGuard -ErrorAction SilentlyContinue | Stop-Process -Force"],
            capture_output=True,
            timeout=5,
        )
        time.sleep(1)
    except Exception:
        pass


def build_executable():
    print("==================================================")
    print("Building ResearchGuard Windows Executable (.EXE)")
    print("SES's R. C. Patel IMRD Shirpur - Central Library")
    print("==================================================")

    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    spec_file = root_dir / "ResearchGuard.spec"

    kill_running_instances()

    # Clean previous build artifacts if present
    if dist_dir.exists():
        print("Cleaning previous dist/ directory...")
        try:
            shutil.rmtree(dist_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning cleaning dist: {e}")

    if build_dir.exists():
        print("Cleaning previous build/ directory...")
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning cleaning build: {e}")

    # Run PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(spec_file),
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root_dir)

    if result.returncode != 0:
        print("[ERROR] PyInstaller build failed with exit code: " + str(result.returncode))
        sys.exit(result.returncode)

    exe_path = dist_dir / "ResearchGuard" / "ResearchGuard.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("==================================================")
        print("[SUCCESS] BUILD COMPLETE!")
        print(f"Executable Output: {exe_path}")
        print(f"File Size: {size_mb:.2f} MB")
        print("Directory Contents:")
        for item in (dist_dir / "ResearchGuard").iterdir():
            if item.is_file() and item.suffix.lower() == ".exe":
                print(f"  - {item.name}")
        print("==================================================")
    else:
        print(f"[ERROR] Expected executable not found at {exe_path}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
