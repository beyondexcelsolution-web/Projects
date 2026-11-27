import os
import sys
import time
import json
import logging
import threading
import tempfile
import subprocess
import requests

from version import APP_VERSION, UPDATE_METADATA_URL, GITHUB_RELEASES_API_URL

logger = logging.getLogger(__name__)

# Global thread-safe state for downloading updates
_download_lock = threading.Lock()
_download_state = {
    'status': 'idle',        # 'idle' | 'downloading' | 'completed' | 'error'
    'progress': 0,           # 0 to 100
    'downloaded_bytes': 0,
    'total_bytes': 0,
    'downloaded_mb': 0.0,
    'total_mb': 0.0,
    'speed': '0 KB/s',
    'error_message': None,
    'file_path': None,
    'version': None
}

def parse_version_tuple(v_str):
    """Parses 'v2.2.0' or '2.2.0' into tuple (2, 2, 0) for safe comparison."""
    clean = str(v_str).strip().lstrip('vV')
    parts = []
    for p in clean.split('.'):
        digits = ''.join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def check_for_updates():
    """
    Checks remote GitHub metadata for newer version.
    Returns structured dict with update info.
    """
    current_tuple = parse_version_tuple(APP_VERSION)
    
    # 1. Try primary UPDATE_METADATA_URL (raw JSON from repo)
    try:
        resp = requests.get(UPDATE_METADATA_URL, timeout=6, headers={'User-Agent': 'CrescentSeatManager-Updater'})
        if resp.status_code == 200:
            data = resp.json()
            remote_v = data.get('version', '0.0.0')
            remote_tuple = parse_version_tuple(remote_v)
            
            is_newer = remote_tuple > current_tuple

            # Check if installer has already been downloaded in TEMP
            temp_dir = tempfile.gettempdir()
            cached_installer = os.path.join(temp_dir, f"Crescent_Setup_v{remote_v}.exe")
            is_downloaded = os.path.exists(cached_installer) and os.path.getsize(cached_installer) >= 20 * 1024 * 1024
            if is_downloaded:
                with _download_lock:
                    _download_state['status'] = 'completed'
                    _download_state['progress'] = 100
                    _download_state['file_path'] = cached_installer
                    _download_state['version'] = remote_v

            return {
                'success': True,
                'update_available': is_newer,
                'current_version': APP_VERSION,
                'latest_version': remote_v,
                'title': data.get('title', f"Release v{remote_v}"),
                'release_date': data.get('release_date', 'Recently released'),
                'summary': data.get('summary', ''),
                'highlights': data.get('highlights', []),
                'download_url': data.get('download_url', ''),
                'filesize_mb': data.get('filesize_mb', '30 MB'),
                'mandatory': data.get('mandatory', False),
                'history': data.get('history', []),
                'is_downloaded': is_downloaded,
                'checked_at': time.strftime("%d-%b-%Y %I:%M %p")
            }
    except Exception as e:
        logger.warning(f"Primary update check failed: {e}")

    # 2. Try GitHub Releases API fallback
    try:
        resp = requests.get(GITHUB_RELEASES_API_URL, timeout=6, headers={'User-Agent': 'CrescentSeatManager-Updater'})
        if resp.status_code == 200:
            rel = resp.json()
            remote_v = rel.get('tag_name', '').lstrip('v')
            remote_tuple = parse_version_tuple(remote_v)
            is_newer = remote_tuple > current_tuple
            
            # Find exe asset
            download_url = ''
            filesize_mb = '30 MB'
            for asset in rel.get('assets', []):
                if asset.get('name', '').endswith('.exe'):
                    download_url = asset.get('browser_download_url', '')
                    size_b = asset.get('size', 0)
                    filesize_mb = f"{size_b / (1024 * 1024):.1f} MB"
                    break
            
            return {
                'success': True,
                'update_available': is_newer,
                'current_version': APP_VERSION,
                'latest_version': remote_v,
                'title': rel.get('name', f"Release v{remote_v}"),
                'release_date': rel.get('published_at', '')[:10],
                'summary': rel.get('body', ''),
                'highlights': [],
                'download_url': download_url,
                'filesize_mb': filesize_mb,
                'mandatory': False,
                'history': [],
                'checked_at': time.strftime("%d-%b-%Y %I:%M %p")
            }
    except Exception as e:
        logger.error(f"Fallback update check failed: {e}")

    return {
        'success': False,
        'update_available': False,
        'current_version': APP_VERSION,
        'error': "Could not connect to update server. Please check internet connection.",
        'checked_at': time.strftime("%d-%b-%Y %I:%M %p")
    }

def get_download_status():
    """Returns current thread-safe download state."""
    with _download_lock:
        return dict(_download_state)

def _download_worker(download_url, target_version):
    global _download_state
    temp_dir = tempfile.gettempdir()
    dest_path = os.path.join(temp_dir, f"Crescent_Setup_v{target_version}.exe")
    
    start_time = time.time()
    try:
        with requests.get(download_url, stream=True, timeout=30, headers={'User-Agent': 'CrescentSeatManager-Updater'}) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with _download_lock:
                _download_state['status'] = 'downloading'
                _download_state['total_bytes'] = total_size
                _download_state['total_mb'] = round(total_size / (1024 * 1024), 2)
                _download_state['downloaded_bytes'] = 0
                _download_state['downloaded_mb'] = 0.0
                _download_state['progress'] = 0
                _download_state['version'] = target_version
                _download_state['error_message'] = None

            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB
            last_speed_check = time.time()
            bytes_since_check = 0

            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    bytes_since_check += len(chunk)

                    now = time.time()
                    elapsed_check = now - last_speed_check
                    speed_str = _download_state.get('speed', '')
                    if elapsed_check >= 0.5:
                        speed_bps = bytes_since_check / elapsed_check
                        if speed_bps >= 1024 * 1024:
                            speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s"
                        else:
                            speed_str = f"{speed_bps / 1024:.0f} KB/s"
                        bytes_since_check = 0
                        last_speed_check = now

                    pct = int((downloaded / total_size) * 100) if total_size > 0 else 50
                    with _download_lock:
                        _download_state['downloaded_bytes'] = downloaded
                        _download_state['downloaded_mb'] = round(downloaded / (1024 * 1024), 2)
                        _download_state['progress'] = pct
                        _download_state['speed'] = speed_str

            with _download_lock:
                _download_state['status'] = 'completed'
                _download_state['progress'] = 100
                _download_state['file_path'] = dest_path

    except Exception as e:
        logger.error(f"Download failed: {e}")
        with _download_lock:
            _download_state['status'] = 'error'
            _download_state['error_message'] = str(e)

def start_update_download(download_url, version_str):
    """Starts background thread to download update installer."""
    with _download_lock:
        if _download_state['status'] == 'downloading':
            return False, "Download already in progress."
        _download_state['status'] = 'downloading'
        _download_state['progress'] = 0
        _download_state['error_message'] = None
        _download_state['file_path'] = None

    t = threading.Thread(target=_download_worker, args=(download_url, version_str), daemon=True)
    t.start()
    return True, "Download started."

def trigger_installer_execution(silent=False):
    """
    Launches downloaded installer so the setup wizard window appears visibly on user's screen.
    Uses native Windows os.startfile (ShellExecute) for full GUI foreground presentation.
    """
    with _download_lock:
        installer_path = _download_state.get('file_path')

    # If file_path is missing or not found in memory, scan temp folder
    if not installer_path or not os.path.exists(installer_path):
        temp_dir = tempfile.gettempdir()
        for fname in os.listdir(temp_dir):
            if fname.startswith("Crescent_Setup_") and fname.endswith(".exe"):
                cand = os.path.join(temp_dir, fname)
                if os.path.getsize(cand) >= 20 * 1024 * 1024:
                    installer_path = cand
                    break

    if not installer_path or not os.path.exists(installer_path):
        return False, "Installer file not found. Please click Download Update."

    logger.info(f"Opening installer wizard: {installer_path}")
    
    # Launch with os.startfile so the setup wizard window pops up in the foreground!
    try:
        os.startfile(installer_path)
    except Exception as e:
        logger.warning(f"os.startfile failed: {e}, falling back to subprocess.Popen")
        subprocess.Popen([installer_path], shell=True)

    # Allow 4 seconds for frontend to receive response and setup wizard to initialize,
    # then exit so Inno Setup can overwrite files without file locks.
    def shutdown_process():
        time.sleep(4)
        os._exit(0)

    threading.Thread(target=shutdown_process, daemon=True).start()
    return True, "Setup Wizard launched on your screen! Please click Next to install."
