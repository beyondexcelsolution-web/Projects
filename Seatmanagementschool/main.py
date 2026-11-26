import os
import sys
import threading
import time
import socket
import webbrowser
import traceback
import ctypes

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_available_port(default_port=5000):
    for p in [default_port, 5001, 5050, 8080, 8888, 5555]:
        if not is_port_in_use(p):
            return p
    return default_port

def show_error_dialog(title, message):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10) # 0x10 = MB_ICONERROR
    except Exception:
        print(f"\n[FATAL ERROR] {title}: {message}\n")

def wait_and_open_browser(port):
    """
    Waits until the server is ACTUALLY accepting connections before launching the browser.
    Prevents 'ERR_CONNECTION_REFUSED' in Chrome/Edge on initial load.
    """
    url = f"http://127.0.0.1:{port}"
    for _ in range(60): # wait up to 12 seconds
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                break
        except Exception:
            time.sleep(0.2)
            
    time.sleep(0.4)
    print(f"\nOpening browser at {url} ...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

def main():
    try:
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("Crescent Islamic High School - Examination Seat Management System")
        except Exception:
            pass

        from paths import get_data_dir
        data_dir = get_data_dir()
        log_file = os.path.join(data_dir, 'app_startup.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Startup initiated at {time.ctime()}\n")
            f.write(f"Data directory: {data_dir}\n")

        print("=" * 72)
        print("      CRESCENT ISLAMIC SCHOOL - SEAT MANAGEMENT SYSTEM")
        print("           Automated Examination Seating Engine")
        print("=" * 72)

        print("\n[1/3] Initializing SQLite database and pre-seeded records...")
        from database import init_db
        init_db()

        print("[2/3] Resolving network port...")
        port = find_available_port(5000)
        print(f"     Bound to port: {port}")

        from app import app
        from waitress import serve

        print(f"[3/3] Starting server at http://127.0.0.1:{port} ...")
        threading.Thread(target=wait_and_open_browser, args=(port,), daemon=True).start()

        print("-" * 72)
        print(f" Application is live at http://127.0.0.1:{port}")
        print(" NOTE: Keep this window open while using the application.")
        print(" To close the application, simply close this window.")
        print("-" * 72 + "\n")

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"Server serving on port {port} at {time.ctime()}\n")

        # Run production waitress server
        serve(app, host='127.0.0.1', port=port, threads=6)

    except Exception as e:
        tb = traceback.format_exc()
        try:
            from paths import get_data_dir
            err_log = os.path.join(get_data_dir(), 'crash_error.log')
            with open(err_log, 'w', encoding='utf-8') as f:
                f.write(tb)
        except Exception:
            pass

        show_error_dialog(
            "Crescent Seat Management - Startup Error",
            f"An error occurred while starting the application:\n\n{str(e)}\n\nPlease contact technical support (7021705408)."
        )
        print("\n" + "=" * 72)
        print("FATAL ERROR ON STARTUP:")
        print(tb)
        print("=" * 72)
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()
