"""
In-App Auto-Update Manager for SolarPulse ERP.
Enables 1-click professional updates from GitHub without user manual download.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import urllib.error
import threading
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

CURRENT_VERSION = "2.0.0"
VERSION_CODE = 20000
BUILD_DATE = "2026-11-27"

# GitHub Raw Manifest URL
GITHUB_OWNER = "beyondexcelsolution-web"
GITHUB_REPO = "Projects"
UPDATE_MANIFEST_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/SolarVendor/version.json"

# Temp folder for update installers
APPDATA_DIR = os.environ.get("APPDATA") or os.path.expanduser("~")
UPDATE_DIR = os.path.join(APPDATA_DIR, "SolarPulseERP", "updates")
os.makedirs(UPDATE_DIR, exist_ok=True)

# In-memory download state
download_state = {
    "status": "idle",       # "idle", "checking", "downloading", "completed", "error"
    "progress_pct": 0,
    "downloaded_bytes": 0,
    "total_bytes": 0,
    "downloaded_mb": 0.0,
    "total_mb": 0.0,
    "speed_mbps": 0.0,
    "error_message": "",
    "installer_path": "",
    "target_version": ""
}
download_lock = threading.Lock()

def parse_version(ver_str: str) -> tuple:
    """Parses '2.1.0' into (2, 1, 0) tuple for accurate comparison."""
    try:
        clean = ver_str.strip().lstrip("vV")
        parts = [int(p) for p in clean.split(".") if p.isdigit()]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])
    except Exception:
        return (0, 0, 0)

def is_newer_version(remote_ver: str, local_ver: str = CURRENT_VERSION) -> bool:
    """Returns True if remote_ver is strictly newer than local_ver."""
    return parse_version(remote_ver) > parse_version(local_ver)

def fetch_remote_manifest(manifest_url: str = UPDATE_MANIFEST_URL) -> Dict[str, Any]:
    """Fetches the latest version manifest JSON from GitHub."""
    req = urllib.request.Request(
        manifest_url,
        headers={"User-Agent": "SolarPulse-ERP-Updater/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError("Version manifest not found on GitHub repository yet.")
        raise RuntimeError(f"GitHub HTTP error: {e.code}")
    except Exception as e:
        raise RuntimeError(f"Unable to connect to GitHub update server: {e}")

def check_for_updates() -> Dict[str, Any]:
    """Checks whether an update is available on GitHub."""
    try:
        manifest = fetch_remote_manifest()
        remote_version = manifest.get("version", CURRENT_VERSION)
        update_available = is_newer_version(remote_version, CURRENT_VERSION)

        return {
            "status": "success",
            "current_version": CURRENT_VERSION,
            "latest_version": remote_version,
            "update_available": update_available,
            "release_date": manifest.get("release_date", ""),
            "release_notes": manifest.get("release_notes", []),
            "download_url": manifest.get("download_url", ""),
            "installer_name": manifest.get("installer_name", "SolarPulse_ERP_Setup_7Day_Demo.exe"),
            "mandatory": manifest.get("mandatory", False),
            "manifest_url": UPDATE_MANIFEST_URL
        }
    except Exception as e:
        return {
            "status": "error",
            "current_version": CURRENT_VERSION,
            "latest_version": CURRENT_VERSION,
            "update_available": False,
            "error": str(e),
            "manifest_url": UPDATE_MANIFEST_URL
        }

def start_background_download(download_url: str, installer_name: str, target_version: str):
    """Starts the download in a background thread."""
    global download_state
    with download_lock:
        if download_state["status"] == "downloading":
            return {"status": "busy", "message": "Download already in progress"}
        download_state["status"] = "downloading"
        download_state["progress_pct"] = 0
        download_state["downloaded_bytes"] = 0
        download_state["total_bytes"] = 0
        download_state["error_message"] = ""
        download_state["target_version"] = target_version

    thread = threading.Thread(
        target=_download_worker,
        args=(download_url, installer_name, target_version),
        daemon=True
    )
    thread.start()
    return {"status": "started", "message": "Download initiated"}

def _download_worker(download_url: str, installer_name: str, target_version: str):
    global download_state
    dest_path = os.path.join(UPDATE_DIR, installer_name or "SolarPulse_ERP_Setup.exe")

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "SolarPulse-ERP-Updater/2.0"}
    )

    try:
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as out_file:
            content_length = resp.headers.get("Content-Length")
            total_bytes = int(content_length) if content_length else 0

            with download_lock:
                download_state["total_bytes"] = total_bytes
                download_state["total_mb"] = round(total_bytes / (1024 * 1024), 2)

            downloaded = 0
            block_size = 64 * 1024  # 64 KB chunk
            last_speed_check = time.time()
            bytes_since_last_check = 0

            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                bytes_since_last_check += len(chunk)

                # Update progress every ~100ms
                now = time.time()
                elapsed = now - last_speed_check
                speed_mbps = 0.0
                if elapsed >= 0.5:
                    speed_mbps = round((bytes_since_last_check / (1024 * 1024)) / elapsed, 2)
                    last_speed_check = now
                    bytes_since_last_check = 0

                pct = round((downloaded / total_bytes) * 100, 1) if total_bytes > 0 else 0

                with download_lock:
                    download_state["downloaded_bytes"] = downloaded
                    download_state["downloaded_mb"] = round(downloaded / (1024 * 1024), 2)
                    download_state["progress_pct"] = pct
                    if speed_mbps > 0:
                        download_state["speed_mbps"] = speed_mbps

        with download_lock:
            download_state["status"] = "completed"
            download_state["progress_pct"] = 100.0
            download_state["installer_path"] = dest_path

    except Exception as e:
        with download_lock:
            download_state["status"] = "error"
            download_state["error_message"] = str(e)

def get_download_progress() -> Dict[str, Any]:
    """Returns the current download progress."""
    with download_lock:
        return dict(download_state)

def launch_installer(silent: bool = False, installer_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Launches the downloaded Inno Setup installer.
    If silent=True, runs with Inno Setup switches:
    /SILENT /SUPPRESSMSGBOXES /FORCECLOSEAPPLICATIONS
    Inno Setup automatically closes old app, updates files, and restarts new version.
    """
    with download_lock:
        target_path = installer_path or download_state.get("installer_path")

        # Fallback: check standard update cache directory
        if not target_path or not os.path.exists(target_path):
            expected = os.path.join(UPDATE_DIR, "SolarPulse_ERP_Setup_7Day_Demo.exe")
            if os.path.exists(expected) and os.path.getsize(expected) > 5 * 1024 * 1024:
                target_path = expected

        if not target_path or not os.path.exists(target_path):
            return {
                "status": "error",
                "message": "Installer file not found on disk. Please click 'Download & Install Update' again."
            }

    try:
        if sys.platform == "win32":
            # Launch via cmd.exe start command so installer runs directly in interactive user session
            if silent:
                cmd = f'start "" "{target_path}" /SILENT /SUPPRESSMSGBOXES /FORCECLOSEAPPLICATIONS'
            else:
                cmd = f'start "" "{target_path}"'
            subprocess.Popen(f'cmd.exe /c {cmd}', shell=True)
        else:
            args = [target_path]
            if silent:
                args.extend(["/SILENT", "/SUPPRESSMSGBOXES", "/FORCECLOSEAPPLICATIONS"])
            subprocess.Popen(args)

        # Allow installer process 2 seconds to initialize, then exit current Python server cleanly
        def delayed_exit():
            time.sleep(2)
            os._exit(0)

        threading.Thread(target=delayed_exit, daemon=True).start()

        return {
            "status": "success",
            "message": "Update installer launched successfully. SolarPulse ERP will restart automatically."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute installer: {e}"}

