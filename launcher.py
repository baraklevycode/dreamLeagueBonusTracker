"""Standalone launcher for Dream League Bonus Tracker.

Opens the browser and starts the FastAPI server.
Designed to be packaged as a .exe with PyInstaller.
"""

import os
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

# Port range to try
PORT_RANGE_START = 8000
PORT_RANGE_END = 8020


def find_free_port() -> int:
    """Find a free port in the configured range.

    Returns:
        The first available port in the range.

    Raises:
        RuntimeError: If no free port is found in the range.
    """
    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found in range {PORT_RANGE_START}-{PORT_RANGE_END}")


def open_browser(port: int) -> None:
    """Wait for the server to start, then open the browser.

    Args:
        port: The port the server is running on.
    """
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


def main() -> None:
    """Launch the Dream League Bonus Tracker."""
    # When running as .exe, set the working directory to the exe location
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))

    # Find a free port
    try:
        port = find_free_port()
    except RuntimeError as e:
        print(f"ERROR: {e}")
        print("Please close other applications using these ports and try again.")
        input("Press Enter to exit...")
        sys.exit(1)

    print("=" * 50)
    print("  Dream League Bonus Tracker")
    print(f"  Starting server on http://127.0.0.1:{port}")
    print("  Opening browser...")
    print("  Close this window to stop the server.")
    print("=" * 50)

    # Open browser in a separate thread
    threading.Thread(target=lambda: open_browser(port), daemon=True).start()

    # Start the server
    uvicorn.run(
        "dream_league_bonus_tracker.api:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
