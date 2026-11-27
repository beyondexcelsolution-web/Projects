"""
Quick Launcher for SolarPulse ERP Web Application.
Starts the server and automatically opens your web browser.
"""

import sys
import os
import io
import time
import socket
import threading
import webbrowser
import logging

# =====================================================================
# Bulletproof stdio redirection for Windows GUI (--windowed) mode
# In PyInstaller --windowed mode, sys.stdout and sys.stderr are None.
# If uvicorn or any logging library accesses sys.stdout.isatty() or writes,
# it throws AttributeError: 'NoneType' object has no attribute 'isatty'.
# =====================================================================

class SafeStream(io.TextIOBase):
    def __init__(self, log_path=None):
        self.log_path = log_path
        self._file = None
        if log_path:
            try:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                self._file = open(log_path, "a", encoding="utf-8", errors="replace")
            except Exception:
                self._file = None

    def write(self, s):
        if self._file:
            try:
                self._file.write(str(s))
                self._file.flush()
            except Exception:
                pass
        return len(str(s))

    def flush(self):
        if self._file:
            try:
                self._file.flush()
            except Exception:
                pass

    def isatty(self):
        return False

    @property
    def encoding(self):
        return "utf-8"

# Setup AppData log directory
appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
log_dir = os.path.join(appdata, "SolarPulseERP")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "solarpulse_server.log")

safe_stream = SafeStream(log_file)

if sys.stdout is None or not hasattr(sys.stdout, "isatty"):
    sys.stdout = safe_stream
if sys.stderr is None or not hasattr(sys.stderr, "isatty"):
    sys.stderr = safe_stream
if sys.stdin is None:
    sys.stdin = io.StringIO()

# Configure basic logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("solarpulse_launcher")

def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port

def open_browser(port: int):
    """Wait for server to bind, then open the browser automatically."""
    url = f"http://127.0.0.1:{port}"
    time.sleep(1.5)
    logger.info(f"Opening browser at: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Could not open browser automatically: {e}")

def main():
    try:
        logger.info("=" * 60)
        logger.info("SolarPulse ERP - Generic Solar Vendor Management Launching")
        logger.info("=" * 60)

        # 1. Initialize Database
        from app.database import init_db
        init_db()
        logger.info("Database initialized successfully.")

        # 2. Find available port
        port = find_available_port(8000)
        logger.info(f"Target server port: {port}")

        # 3. Import app and launch browser
        from main import app
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

        # 4. Start Uvicorn Server with log_config=None to prevent PyInstaller dictConfig crash
        import uvicorn
        logger.info(f"Starting uvicorn server on http://127.0.0.1:{port}")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            log_config=None  # Prevents uvicorn.logging.DefaultFormatter AttributeError on isatty
        )
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        logger.critical(f"Server launch failed:\n{err_msg}")
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"SolarPulse ERP failed to start:\n\n{e}\n\nPlease check logs at:\n{log_file}",
                "SolarPulse ERP - Startup Error",
                0x10 # MB_ICONERROR
            )
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
