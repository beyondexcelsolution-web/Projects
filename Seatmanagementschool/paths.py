import os
import sys
import shutil

def get_base_dir():
    """
    Returns the read-only directory containing bundled assets (templates, static, seed data).
    When frozen with PyInstaller, this is sys._MEIPASS.
    When running in development, this is the project directory.
    """
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.abspath(os.path.dirname(__file__))

def get_data_dir():
    """
    Returns the writable directory for persistent data (database, uploads, exports).
    When frozen, this uses %LOCALAPPDATA% so that standard users never encounter
    PermissionError / Access is denied in C:\\Program Files.
    """
    if getattr(sys, 'frozen', False):
        local_app_data = os.environ.get('LOCALAPPDATA')
        if not local_app_data:
            local_app_data = os.path.expanduser('~')
        data_dir = os.path.join(local_app_data, 'CrescentSeatManagement')
        try:
            os.makedirs(data_dir, exist_ok=True)
            return data_dir
        except Exception:
            home_dir = os.path.join(os.path.expanduser('~'), '.crescent_seat_management')
            os.makedirs(home_dir, exist_ok=True)
            return home_dir

    return os.path.abspath(os.path.dirname(__file__))

def get_db_path():
    """
    Returns the path to the SQLite database.
    If the database doesn't exist in data_dir, it automatically copies
    the clean initial database. Once target_db exists, it is NEVER overwritten.
    """
    data_dir = get_data_dir()
    target_db = os.path.join(data_dir, 'instance', 'school_seats.db')
    base_dir = get_base_dir()
    bundled_db = os.path.join(base_dir, 'instance', 'school_seats.db')

    if not os.path.exists(target_db):
        os.makedirs(os.path.dirname(target_db), exist_ok=True)
        if os.path.exists(bundled_db):
            try:
                shutil.copy2(bundled_db, target_db)
            except Exception:
                pass

    return target_db

def get_exports_dir():
    data_dir = get_data_dir()
    exports_dir = os.path.join(data_dir, 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    return exports_dir

def get_uploads_dir():
    data_dir = get_data_dir()
    uploads_dir = os.path.join(data_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir
