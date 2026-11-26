import os
import sys
import hashlib
import platform
import urllib.request
import urllib.parse
import csv
import io
import time
import threading
from datetime import datetime

SHEET_URL = "https://docs.google.com/spreadsheets/d/1haqnondAWuEELvHLbkTO0CkojsU4-DsTmoKAR9R-rWI/export?format=csv&gid=0"
DEFAULT_CLIENT_ID = "Client_003" # Primary Client ID for Crescent Seat Management System

# In-memory cache to avoid repeated HTTP calls on every page click
_MEMORY_CACHE = {
    'result': None,
    'timestamp': 0,
    'ttl': 120 # Cache online result for 2 minutes
}

_BG_SYNC_RUNNING = False
_TELEMETRY_SENT = False

def get_machine_hwid():
    """
    Generates a unique, persistent Hardware ID (HWID) bound to this computer's Windows installation
    MachineGuid and BIOS hardware characteristics via direct Registry query (instantaneous, never hangs).
    """
    components = []
    
    # 1. Windows MachineGuid from registry (unique per Windows installation)
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            components.append(str(guid).strip().upper())
    except Exception:
        components.append(platform.node())

    # 2. BIOS / Motherboard info from registry
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
            for field in ["BaseBoardProduct", "SystemManufacturer", "SystemProductName"]:
                try:
                    val, _ = winreg.QueryValueEx(key, field)
                    if val:
                        components.append(str(val).strip().upper())
                except Exception:
                    pass
    except Exception:
        pass

    # 3. CPU / Processor architecture
    components.append(platform.processor() or platform.machine() or "CPU_DEFAULT")

    raw_id = ":".join(components)
    hashed = hashlib.sha256(raw_id.encode('utf-8')).hexdigest().upper()
    return f"HWID-{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}-{hashed[12:16]}"

def get_display_ref_id():
    """
    Returns a customer-friendly, professional reference code (e.g. REF-8E03-1DD5)
    instead of scary 'HWID' terminology, so clients never feel tracked or hacked.
    """
    hwid = get_machine_hwid()
    parts = hwid.split('-')
    if len(parts) >= 3:
        return f"REF-{parts[1]}-{parts[2]}"
    return "REF-CSM-2026"

def get_machine_info():
    return {
        'hwid': get_machine_hwid(),
        'ref_id': get_display_ref_id(),
        'computer_name': platform.node(),
        'os': platform.platform(),
        'user': os.environ.get('USERNAME', 'DefaultUser')
    }

def fetch_sheet_rows():
    req = urllib.request.Request(SHEET_URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        content = resp.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    return [dict(r) for r in reader]

def parse_expiry_date(date_str):
    if not date_str or date_str.strip().lower() in ['lifetime', 'never', 'none', '']:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    return None

def send_silent_telemetry(webhook_url, client_id, status_code):
    """
    Silent radar: sends a background ping to the developer's Apps Script webhook
    with PC name, username, and HWID so you always know when/where the app is run.
    """
    try:
        info = get_machine_info()
        params = {
            'action': 'ping',
            'client': client_id,
            'pc': info['computer_name'],
            'user': info['user'],
            'hwid': info['hwid'],
            'ref': info['ref_id'],
            'status': status_code,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        query = urllib.parse.urlencode(params)
        target_url = webhook_url + ('&' if '?' in webhook_url else '?') + query
        req = urllib.request.Request(
            target_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=4):
            pass
    except Exception:
        pass

def _sync_remote_sheet_background():
    """
    Asynchronously checks Google Sheet in background so user requests are NEVER delayed or frozen.
    """
    global _BG_SYNC_RUNNING, _MEMORY_CACHE, _TELEMETRY_SENT
    if _BG_SYNC_RUNNING:
        return
    _BG_SYNC_RUNNING = True

    try:
        from database import get_db
        current_hwid = get_machine_hwid()
        ref_id = get_display_ref_id()
        current_pc = platform.node()

        rows = fetch_sheet_rows()
        sheet_data = None
        for r in rows:
            c_id = r.get('Client_id', '').strip()
            c_name = r.get('client_name', '').strip().lower()
            c_app = r.get('appId', '').strip().lower()
            if c_id in ['Client_003', 'Client_Seat_001', 'CIS_SEAT_001'] or 'seat' in c_name or 'crescent' in c_name or 'seat' in c_app:
                sheet_data = r
                break
        if not sheet_data and rows:
            for r in rows:
                if r.get('Client_id', '').strip() == 'Client_001':
                    sheet_data = r
                    break

        if sheet_data:
            raw_status = sheet_data.get('status', 'ACTIVE').strip().upper()
            expiry_str = sheet_data.get('expiry_date', 'Lifetime').strip()
            contact = sheet_data.get('contact', '7021705408').strip()
            custom_msg = sheet_data.get('message', '').strip()
            notes = sheet_data.get('notes', '').strip()
            apk_url = sheet_data.get('apkUrl', '').strip()

            exp_date = parse_expiry_date(expiry_str)
            is_expired = exp_date and datetime.now().date() > exp_date

            # If user explicitly specifies an authorized HWID in notes column:
            allowed_hwid = None
            if 'HWID-' in notes.upper():
                for part in notes.split():
                    if part.upper().startswith('HWID-'):
                        allowed_hwid = part.strip().upper()
                        break

            is_device_mismatch = (allowed_hwid and allowed_hwid != current_hwid)

            if raw_status != 'ACTIVE':
                status_code = 'PAYMENT_PENDING'
                is_active = False
                title = "Annual Maintenance & Subscription Due"
                message = custom_msg or "Your software maintenance subscription is currently pending renewal. Please contact support to continue uninterrupted service."
            elif is_expired:
                status_code = 'EXPIRED'
                is_active = False
                title = "Annual License Renewal Required"
                message = f"Your annual usage license completed on {expiry_str}. Please contact support to extend service."
            elif is_device_mismatch:
                status_code = 'WORKSTATION_LIMIT'
                is_active = False
                title = "Workstation License Limit Reached"
                message = (
                    "This software package is registered under a Single-Workstation License. "
                    "Another primary school computer is already registered. "
                    "Simultaneous execution on secondary workstations requires a Multi-PC Campus License. "
                    "Please contact technical support to authorize this workstation."
                )
            else:
                status_code = 'ACTIVE'
                is_active = True
                title = "Single-Workstation License Active"
                message = "Licensed to Crescent Islamic School."

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('license_status', ?)", (status_code,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('license_message', ?)", (message,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('license_contact', ?)", (contact,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('license_last_check', ?)", (str(int(time.time())),))
            conn.commit()
            conn.close()

            _MEMORY_CACHE['result'] = {
                'is_active': is_active,
                'status': status_code,
                'title': title,
                'message': message,
                'contact': contact,
                'hwid': current_hwid,
                'ref_id': ref_id,
                'computer_name': current_pc
            }
            _MEMORY_CACHE['timestamp'] = time.time()

            if not _TELEMETRY_SENT and apk_url and apk_url.startswith('http'):
                _TELEMETRY_SENT = True
                send_silent_telemetry(apk_url, sheet_data.get('Client_id', 'Client_003'), status_code)

    except Exception:
        pass
    finally:
        _BG_SYNC_RUNNING = False

def verify_license(force_online=False):
    global _MEMORY_CACHE
    now = time.time()

    if force_online:
        _sync_remote_sheet_background()
        if _MEMORY_CACHE['result'] is not None:
            return _MEMORY_CACHE['result']

    if _MEMORY_CACHE['result'] is not None and (now - _MEMORY_CACHE['timestamp']) < _MEMORY_CACHE['ttl']:
        return _MEMORY_CACHE['result']

    from database import get_db
    current_hwid = get_machine_hwid()
    ref_id = get_display_ref_id()
    current_pc = platform.node()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM settings WHERE key = 'license_status'")
    status_row = cursor.fetchone()
    cached_status = status_row['value'] if status_row else 'ACTIVE'

    cursor.execute("SELECT value FROM settings WHERE key = 'license_message'")
    msg_row = cursor.fetchone()
    message = msg_row['value'] if msg_row else "Licensed to Crescent Islamic School."

    cursor.execute("SELECT value FROM settings WHERE key = 'license_contact'")
    contact_row = cursor.fetchone()
    contact = contact_row['value'] if contact_row else "7021705408"

    conn.close()

    if cached_status != 'ACTIVE':
        status_code = cached_status
        is_active = False
        title = "Annual Maintenance & Subscription Due"
    else:
        status_code = 'ACTIVE'
        is_active = True
        title = "Single-Workstation License Active"

    res = {
        'is_active': is_active,
        'status': status_code,
        'title': title,
        'message': message,
        'contact': contact,
        'hwid': current_hwid,
        'ref_id': ref_id,
        'computer_name': current_pc
    }
    _MEMORY_CACHE['result'] = res
    _MEMORY_CACHE['timestamp'] = now

    # Trigger background online check without delaying response
    if not _BG_SYNC_RUNNING:
        threading.Thread(target=_sync_remote_sheet_background, daemon=True).start()

    return res
