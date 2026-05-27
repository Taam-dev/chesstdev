#!/usr/bin/env python3
"""
Download the correct Stockfish binary for the current platform.
"""

import os
import sys
import platform
import zipfile
import tarfile
import urllib.request
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

STOCKFISH_VERSION = "16.1"
ENGINES_DIR = Path(__file__).parent.parent / "assets" / "engines"

DOWNLOAD_URLS = {
    "windows_x64": (
        f"https://github.com/official-stockfish/Stockfish/releases/download/"
        f"sf_{STOCKFISH_VERSION}/stockfish-windows-x86-64-avx2.zip",
        "stockfish.exe",
    ),
    "linux_x64": (
        f"https://github.com/official-stockfish/Stockfish/releases/download/"
        f"sf_{STOCKFISH_VERSION}/stockfish-ubuntu-x86-64-avx2.tar",
        "stockfish",
    ),
    "macos_arm64": (
        f"https://github.com/official-stockfish/Stockfish/releases/download/"
        f"sf_{STOCKFISH_VERSION}/stockfish-macos-m1-apple-silicon.tar",
        "stockfish",
    ),
    "macos_x64": (
        f"https://github.com/official-stockfish/Stockfish/releases/download/"
        f"sf_{STOCKFISH_VERSION}/stockfish-macos-x86-64-modern.tar",
        "stockfish",
    ),
}


def get_platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return "windows_x64"
    elif system == "linux":
        return "linux_x64"
    elif system == "darwin":
        return "macos_arm64" if "arm" in machine else "macos_x64"
    else:
        print(f"❌ Unsupported platform: {system}")
        sys.exit(1)


def download_with_progress(url: str, dest: Path) -> None:
    print(f"  Downloading from:\n  {url}")

    def progress(block_num, block_size, total_size):
        if total_size > 0:
            pct = min(block_num * block_size / total_size * 100, 100)
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"\r  [{bar}] {pct:.1f}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print()


def extract_binary(archive: Path, binary_name: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)

    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            # Find the binary inside
            for member in zf.namelist():
                if member.endswith(binary_name):
                    zf.extract(member, dest_dir)
                    extracted = dest_dir / member
                    final = dest_dir / binary_name
                    extracted.rename(final)
                    return final
    else:
        with tarfile.open(archive) as tf:
            for member in tf.getmembers():
                if member.name.endswith(binary_name):
                    member.name = binary_name
                    tf.extract(member, dest_dir)
                    return dest_dir / binary_name

    raise FileNotFoundError(f"Binary '{binary_name}' not found in archive")


def main():
    ENGINES_DIR.mkdir(parents=True, exist_ok=True)

    key = get_platform_key()
    url, binary_name = DOWNLOAD_URLS[key]
    final_path = ENGINES_DIR / binary_name

    if final_path.exists():
        print(f"✅ Stockfish already exists at: {final_path}")
        return

    print(f"📥 Downloading Stockfish {STOCKFISH_VERSION} for {key}...")

    archive_name = url.split("/")[-1]
    archive_path = ENGINES_DIR / archive_name

    try:
        download_with_progress(url, archive_path)
        print("📦 Extracting...")
        binary = extract_binary(archive_path, binary_name, ENGINES_DIR)

        # Make executable on Unix
        if platform.system() != "Windows":
            binary.chmod(0o755)

        archive_path.unlink()  # Cleanup archive
        print(f"✅ Stockfish installed at: {binary}")

    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("\n  Manual install options:")
        print("  • Linux:   sudo apt install stockfish")
        print("  • macOS:   brew install stockfish")
        print("  • Windows: https://stockfishchess.org/download/")
        sys.exit(1)


if __name__ == "__main__":
    main()
