import sqlite3
import os
import json
from paths import get_db_path

def get_db():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    # 2. Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adm_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        seating_group TEXT DEFAULT '',
        gender TEXT CHECK(gender IN ('M', 'F')) DEFAULT 'M',
        block TEXT DEFAULT 'Boys Block',
        roll_in_group INTEGER DEFAULT 0,
        roll_in_class INTEGER DEFAULT 0,
        stream TEXT DEFAULT '',
        is_hifz INTEGER DEFAULT 0,
        is_hindi INTEGER DEFAULT 0,
        is_urdu INTEGER DEFAULT 0,
        is_telugu_exempt INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1
    )
    ''')

    # 3. Rooms Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        block TEXT NOT NULL,
        benches INTEGER NOT NULL,
        seats_per_bench INTEGER DEFAULT 2,
        floor TEXT DEFAULT 'Ground Floor',
        print_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # 4. Arrangements Table (Block-by-Block Plan)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS arrangements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT NOT NULL,
        row_side TEXT CHECK(row_side IN ('L', 'R')) NOT NULL,
        class_or_group TEXT NOT NULL,
        from_roll INTEGER NOT NULL,
        to_roll INTEGER NOT NULL,
        sort_order INTEGER DEFAULT 0
    )
    ''')

    # Default Settings Values
    default_settings = {
        'school_name': 'Crescent Islamic School',
        'exam_title': 'Periodic Assessment – 2',
        'academic_year': '2026-27',
        'first_exam_date': '2026-11-16',
        'class_print_order': 'Section first',
        'attendance_dates_json': json.dumps([
            {'col': 1, 'date': '01/9', 'day': 'THUR'},
            {'col': 2, 'date': '03/9', 'day': 'SAT'},
            {'col': 3, 'date': '05/9', 'day': 'MON'},
            {'col': 4, 'date': '06/9', 'day': 'TUE'},
            {'col': 5, 'date': '07/9', 'day': 'WED'},
            {'col': 6, 'date': '08/9', 'day': 'THUR'},
            {'col': 7, 'date': '09/9', 'day': 'FRI'},
            {'col': 8, 'date': '10/9', 'day': 'SAT'}
        ]),
        'license_contact': '7021705408'
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
