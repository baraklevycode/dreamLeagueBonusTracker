"""Build script to create the .exe using PyInstaller."""

import subprocess
import sys


def main() -> None:
    """Run PyInstaller to build the .exe."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "DreamLeagueBonusTracker",
        "--onedir",
        "--console",
        "--add-data", "static;static",
        "--add-data", ".env.example;.",
        "--hidden-import", "dream_league_bonus_tracker",
        "--hidden-import", "dream_league_bonus_tracker.api",
        "--hidden-import", "dream_league_bonus_tracker.client",
        "--hidden-import", "dream_league_bonus_tracker.config",
        "--hidden-import", "dream_league_bonus_tracker.models",
        "--hidden-import", "dream_league_bonus_tracker.service",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--collect-submodules", "uvicorn",
        "--collect-submodules", "fastapi",
        "--collect-submodules", "starlette",
        "--collect-submodules", "pydantic",
        "--collect-submodules", "httpx",
        "--noconfirm",
        "launcher.py",
    ]

    print("Building .exe...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print()
    print("=" * 50)
    print("  Build complete!")
    print("  Output: dist/DreamLeagueBonusTracker/")
    print("  Run: dist/DreamLeagueBonusTracker/DreamLeagueBonusTracker.exe")
    print("=" * 50)


if __name__ == "__main__":
    main()
