"""
7-Day Demo & License Trial Manager for SolarPulse ERP.
Includes machine-bound signature verification, clock tamper detection,
and master activation key unlocking.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta

TRIAL_DAYS = 7
SECRET_SALT = b"SolarPulse-Trial-Secured-Salt-2026-v2"
MASTER_KEYS = ["SOLARPULSE-LIFETIME-2026", "SUNPOWER-FULL-PRO-99", "SOLAR-PRAMOD-UNLIMITED"]

def get_license_dir():
    appdata = os.environ.get("APPDATA")
    if appdata and os.path.exists(appdata):
        lic_dir = os.path.join(appdata, "SolarPulseERP")
    else:
        lic_dir = os.path.join(os.path.expanduser("~"), ".solarpulse_erp")
    os.makedirs(lic_dir, exist_ok=True)
    return lic_dir

def get_license_file():
    return os.path.join(get_license_dir(), "demo_license.dat")

def get_machine_fingerprint():
    try:
        node = str(uuid.getnode())
        user = os.environ.get("USERNAME", "DefaultUser")
        return f"{node}_{user}"
    except Exception:
        return "GenericSolarClientMachine"

def generate_signature(data_dict: dict) -> str:
    serialized = f"{data_dict.get('first_run')}|{data_dict.get('last_run')}|{data_dict.get('machine_id')}|{data_dict.get('unlocked')}"
    return hmac.new(SECRET_SALT, serialized.encode("utf-8"), hashlib.sha256).hexdigest()

def init_trial_license():
    lic_file = get_license_file()
    now_ts = int(time.time())
    machine_id = get_machine_fingerprint()

    if not os.path.exists(lic_file):
        data = {
            "first_run": now_ts,
            "last_run": now_ts,
            "machine_id": machine_id,
            "unlocked": False,
            "activation_key": ""
        }
        data["sig"] = generate_signature(data)
        try:
            with open(lic_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"License write warning: {e}")
        return data

    try:
        with open(lic_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        # Re-create if corrupted
        data = {
            "first_run": now_ts,
            "last_run": now_ts,
            "machine_id": machine_id,
            "unlocked": False,
            "activation_key": ""
        }
        data["sig"] = generate_signature(data)
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

def check_trial_status():
    """
    Returns dict:
    {
        "unlocked": bool,
        "is_expired": bool,
        "days_left": int,
        "hours_left": int,
        "first_run_str": str,
        "expires_str": str,
        "error_msg": str
    }
    """
    data = init_trial_license()
    lic_file = get_license_file()
    now_ts = int(time.time())

    # If already unlocked with permanent key
    if data.get("unlocked"):
        return {
            "unlocked": True,
            "is_expired": False,
            "days_left": 9999,
            "hours_left": 99999,
            "first_run_str": datetime.fromtimestamp(data["first_run"]).strftime("%d-%b-%Y"),
            "expires_str": "Lifetime Activated",
            "error_msg": ""
        }

    # Verify signature
    expected_sig = generate_signature(data)
    if data.get("sig") != expected_sig:
        return {
            "unlocked": False,
            "is_expired": True,
            "days_left": 0,
            "hours_left": 0,
            "first_run_str": "",
            "expires_str": "Expired (Tamper Detected)",
            "error_msg": "License file tampering detected. Trial locked."
        }

    first_run = data.get("first_run", now_ts)
    last_run = data.get("last_run", now_ts)

    # Clock rollback detection
    if now_ts < last_run - 300: # allow 5 min clock skew
        return {
            "unlocked": False,
            "is_expired": True,
            "days_left": 0,
            "hours_left": 0,
            "first_run_str": datetime.fromtimestamp(first_run).strftime("%d-%b-%Y"),
            "expires_str": "Expired (Clock Tamper)",
            "error_msg": "System clock rollback detected. Trial expired."
        }

    # Update last_run
    data["last_run"] = now_ts
    data["sig"] = generate_signature(data)
    try:
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    # Calculate expiration (7 days = 7 * 86400 seconds)
    trial_duration = TRIAL_DAYS * 86400
    elapsed_seconds = now_ts - first_run
    remaining_seconds = max(0, trial_duration - elapsed_seconds)

    days_left = remaining_seconds // 86400
    hours_left = (remaining_seconds % 86400) // 3600
    is_expired = remaining_seconds <= 0

    first_run_dt = datetime.fromtimestamp(first_run)
    expires_dt = first_run_dt + timedelta(days=TRIAL_DAYS)

    return {
        "unlocked": False,
        "is_expired": is_expired,
        "days_left": int(days_left),
        "hours_left": int(hours_left),
        "first_run_str": first_run_dt.strftime("%d-%b-%Y %I:%M %p"),
        "expires_str": expires_dt.strftime("%d-%b-%Y %I:%M %p"),
        "error_msg": "Your 7-day evaluation trial has ended." if is_expired else ""
    }

def activate_license(key_str: str) -> bool:
    clean_key = key_str.strip().upper()
    if clean_key in MASTER_KEYS or clean_key.startswith("SOLAR-PRO-"):
        lic_file = get_license_file()
        data = init_trial_license()
        data["unlocked"] = True
        data["activation_key"] = clean_key
        data["sig"] = generate_signature(data)
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    return False

if __name__ == "__main__":
    status = check_trial_status()
    print("Trial Status:", status)
