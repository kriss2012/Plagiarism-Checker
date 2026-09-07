"""One-click Windows executable build and packaging script for ResearchGuard."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_executable():
    print("==================================================")
    print("Building ResearchGuard Windows Executable (.EXE)")
    print("==================================================")

    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    spec_file = root_dir / "ResearchGuard.spec"

    # Clean previous build artifacts if present
    if dist_dir.exists():
        print("Cleaning previous dist/ directory...")
        shutil.rmtree(dist_dir, ignore_errors=True)

    if build_dir.exists():
        print("Cleaning previous build/ directory...")
        shutil.rmtree(build_dir, ignore_errors=True)

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
        print("❌ Error: PyInstaller build failed!")
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
