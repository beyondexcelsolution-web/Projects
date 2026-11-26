from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import json
from collections import defaultdict
from werkzeug.utils import secure_filename

from paths import get_base_dir, get_data_dir, get_exports_dir, get_uploads_dir
from database import init_db, get_db
from seating_engine import get_seating_plan_data
from excel_importer import import_students_from_excel
from license_manager import verify_license, get_machine_hwid
from docx_exporter import (
    generate_class_plan_docx,
    generate_roomwise_display_docx,
    generate_attendance_sheet_docx,
    generate_master_summary_docx
)
from excel_exporter import generate_master_excel
from consolidated_engine import (
    get_consolidated_sheet_data,
    generate_consolidated_excel,
    generate_consolidated_docx
)

app = Flask(
    __name__,
    template_folder=os.path.join(get_base_dir(), 'templates'),
    static_folder=os.path.join(get_base_dir(), 'static')
)
app.secret_key = 'crescent-school-seating-system-secret-key-2026'

# Remote License & Device Verification Hook
@app.before_request
def check_app_lock():
    if request.path.startswith('/static') or request.endpoint == 'refresh_license':
        return
    lic = verify_license()
    if not lic['is_active']:
        return render_template('locked.html', lic=lic), 403

@app.route('/license/refresh', methods=['GET', 'POST'])
def refresh_license():
    lic = verify_license(force_online=True)
    if lic['is_active']:
        flash("License verified successfully! Access granted.", "success")
        return redirect(url_for('dashboard'))
    else:
        return render_template('locked.html', lic=lic), 403

@app.context_processor
def inject_global_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return {
        'request_hwid': get_machine_hwid(),
        'app_settings': settings
    }

with app.app_context():
    init_db()

# ==============================================================================
# DASHBOARD
# ==============================================================================
@app.route('/')
def dashboard():
    plan_data = get_seating_plan_data()
    return render_template(
        'dashboard.html',
        settings=plan_data['settings'],
        checks=plan_data['system_checks'],
        rooms=plan_data['rooms_summary'],
        classes=plan_data['classes_plan']
    )

def to_iso_date(d_str):
    if not d_str:
        return ''
    d_str = str(d_str).strip()
    if '-' in d_str and len(d_str) == 10:
        return d_str
    if '/' in d_str:
        parts = d_str.split('/')
        if len(parts) == 3:
            return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        elif len(parts) == 2:
            return f"2026-{int(parts[1]):02d}-{int(parts[0]):02d}"
    return d_str

# ==============================================================================
# SETTINGS / ASSESSMENT MANAGEMENT
# ==============================================================================
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        exam_title = request.form.get('exam_title', 'Periodic Assessment – 2').strip()
        academic_year = request.form.get('academic_year', '2026-27').strip()
        first_exam_date = request.form.get('first_exam_date', '2026-11-16').strip()
        class_print_order = request.form.get('class_print_order', 'Section first')

        # Read Attendance Date & Day Columns dynamically (supports any number of days)
        dates_list = []
        date_inputs = request.form.getlist('dates[]')
        day_inputs = request.form.getlist('days[]')

        if date_inputs:
            for idx, (d_val, day_val) in enumerate(zip(date_inputs, day_inputs), 1):
                d_val = (d_val or '').strip()
                day_val = (day_val or '').strip()
                if d_val or day_val:
                    dates_list.append({'col': idx, 'date': d_val, 'day': day_val})
        else:
            # Fallback check for date_1, date_2...
            i = 1
            while True:
                key_d = f'date_{i}'
                if key_d not in request.form and i > 8:
                    break
                d_val = request.form.get(key_d, '').strip()
                day_val = request.form.get(f'day_{i}', '').strip()
                if d_val or day_val or (i <= 8 and f'day_{i}' in request.form):
                    dates_list.append({'col': i, 'date': d_val, 'day': day_val})
                i += 1

        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('exam_title', ?)", (exam_title,))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('academic_year', ?)", (academic_year,))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('first_exam_date', ?)", (first_exam_date,))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('class_print_order', ?)", (class_print_order,))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('attendance_dates_json', ?)", (json.dumps(dates_list),))
        conn.commit()
        conn.close()

        flash("Exam settings and attendance dates saved successfully!", "success")
        return redirect(url_for('settings'))

    cursor.execute("SELECT key, value FROM settings")
    settings_dict = {row['key']: row['value'] for row in cursor.fetchall()}
    try:
        attendance_dates = json.loads(settings_dict.get('attendance_dates_json', '[]'))
    except Exception:
        attendance_dates = []

    # If never set, default to 8 days, but if user saved custom days (e.g. 5, 10), keep their exact list!
    if not attendance_dates:
        default_days = [
            ('01/9', 'THUR'), ('03/9', 'SAT'), ('05/9', 'MON'), ('06/9', 'TUE'),
            ('07/9', 'WED'), ('08/9', 'THUR'), ('09/9', 'FRI'), ('10/9', 'SAT')
        ]
        attendance_dates = [{'col': i + 1, 'date': d, 'day': dy} for i, (d, dy) in enumerate(default_days)]

    first_exam_date_iso = to_iso_date(settings_dict.get('first_exam_date', '2026-11-16'))
    for item in attendance_dates:
        item['date_iso'] = to_iso_date(item.get('date', ''))

    conn.close()
    return render_template(
        'settings.html',
        settings=settings_dict,
        attendance_dates=attendance_dates,
        first_exam_date_iso=first_exam_date_iso
    )

# ==============================================================================
# STUDENTS DIRECTORY (FULL CRUD + UPLOAD)
# ==============================================================================
@app.route('/students')
def students():
    q = request.args.get('q', '').strip()
    cls_filter = request.args.get('class', '').strip()
    gender_filter = request.args.get('gender', '').strip()
    block_filter = request.args.get('block', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM students WHERE active = 1"
    params = []

    if q:
        query += " AND (name LIKE ? OR adm_no LIKE ? OR CAST(roll_in_class AS TEXT) LIKE ? OR CAST(roll_in_group AS TEXT) LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])
    if cls_filter:
        query += " AND (class_name = ? OR seating_group = ?)"
        params.extend([cls_filter, cls_filter])
    if gender_filter:
        query += " AND gender = ?"
        params.append(gender_filter)
    if block_filter:
        query += " AND block = ?"
        params.append(block_filter)

    query += " ORDER BY class_name ASC, roll_in_class ASC, adm_no ASC"
    cursor.execute(query, params)
    student_list = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT class_name FROM students WHERE active = 1 ORDER BY class_name ASC")
    classes = [r['class_name'] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT seating_group FROM students WHERE seating_group != '' AND active = 1 ORDER BY seating_group ASC")
    groups = [r['seating_group'] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT block FROM students WHERE active = 1 AND block IS NOT NULL AND block != '' ORDER BY block ASC")
    blocks = [r['block'] for r in cursor.fetchall()]

    conn.close()
    return render_template(
        'students.html',
        students=student_list,
        classes=classes,
        groups=groups,
        blocks=blocks,
        q=q,
        current_class=cls_filter,
        current_gender=gender_filter,
        current_block=block_filter
    )

@app.route('/students/add', methods=['POST'])
def add_student():
    adm_no = request.form.get('adm_no', '').strip().upper()
    name = request.form.get('name', '').strip()
    class_name = request.form.get('class_name', '').strip()
    seating_group = request.form.get('seating_group', '').strip()
    gender = request.form.get('gender', 'M')
    block = request.form.get('block', 'Boys Block')
    is_hifz = 1 if request.form.get('is_hifz') else 0
    is_hindi = 1 if request.form.get('is_hindi') else 0

    roll_in_class_raw = request.form.get('roll_in_class', '').strip()
    roll_in_group_raw = request.form.get('roll_in_group', '').strip()

    if not adm_no or not name or not class_name:
        flash("Admission number, name, and class are required.", "danger")
        return redirect(url_for('students'))

    conn = get_db()
    cursor = conn.cursor()

    # Determine roll in class
    if roll_in_class_raw and roll_in_class_raw.isdigit() and int(roll_in_class_raw) > 0:
        roll_cls = int(roll_in_class_raw)
    else:
        cursor.execute("SELECT MAX(roll_in_class) FROM students WHERE class_name = ?", (class_name,))
        max_roll = cursor.fetchone()[0] or 0
        roll_cls = max_roll + 1

    # Determine roll in group
    if roll_in_group_raw and roll_in_group_raw.isdigit() and int(roll_in_group_raw) > 0:
        roll_grp = int(roll_in_group_raw)
    else:
        used_grp = seating_group if seating_group else class_name
        cursor.execute("SELECT MAX(roll_in_group) FROM students WHERE (seating_group = ? OR class_name = ?)", (used_grp, used_grp))
        max_grp_roll = cursor.fetchone()[0] or 0
        roll_grp = max_grp_roll + 1

    try:
        cursor.execute('''
        INSERT INTO students (
            adm_no, name, class_name, seating_group, gender, block,
            roll_in_group, roll_in_class, is_hifz, is_hindi, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (adm_no, name, class_name, seating_group, gender, block, roll_grp, roll_cls, is_hifz, is_hindi))
        conn.commit()
        flash(f"Student {name} ({adm_no}) added successfully!", "success")
    except Exception as e:
        flash(f"Error adding student: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('students'))

@app.route('/students/edit/<int:student_id>', methods=['POST'])
def edit_student(student_id):
    name = request.form.get('name', '').strip()
    class_name = request.form.get('class_name', '').strip()
    seating_group = request.form.get('seating_group', '').strip()
    roll_in_class = request.form.get('roll_in_class', 0, type=int)
    roll_in_group = request.form.get('roll_in_group', 0, type=int)
    gender = request.form.get('gender', 'M')
    block = request.form.get('block', 'Boys Block')
    is_hifz = 1 if request.form.get('is_hifz') else 0
    is_hindi = 1 if request.form.get('is_hindi') else 0

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE students SET
        name = ?, class_name = ?, seating_group = ?, roll_in_class = ?,
        roll_in_group = ?, gender = ?, block = ?, is_hifz = ?, is_hindi = ?
    WHERE id = ?
    ''', (name, class_name, seating_group, roll_in_class, roll_in_group, gender, block, is_hifz, is_hindi, student_id))
    conn.commit()
    conn.close()

    flash("Student details updated successfully!", "success")
    return redirect(url_for('students'))

@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    flash("Student removed from database.", "info")
    return redirect(url_for('students'))

@app.route('/students/bulk-delete', methods=['POST'])
def bulk_delete_students():
    student_ids = request.form.getlist('selected_ids')
    if not student_ids and request.is_json:
        student_ids = request.json.get('student_ids', [])
    if not student_ids:
        raw_ids = request.form.get('ids_csv', '').strip()
        if raw_ids:
            student_ids = [x.strip() for x in raw_ids.split(',') if x.strip()]

    if not student_ids:
        flash("No students were selected for deletion.", "warning")
        return redirect(url_for('students'))

    conn = get_db()
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(student_ids))
    cursor.execute(f"DELETE FROM students WHERE id IN ({placeholders})", student_ids)
    count = cursor.rowcount
    conn.commit()
    conn.close()

    flash(f"Successfully deleted {count} selected student(s) from database.", "success")
    return redirect(url_for('students'))

@app.route('/system/reset-data', methods=['POST'])
def reset_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students")
    cursor.execute("DELETE FROM arrangements")
    conn.commit()
    conn.close()
    flash("Database cleaned successfully! All students and seating arrangements have been reset. You can now import a clean test sheet.", "success")
    return redirect(url_for('settings'))

@app.route('/students/upload', methods=['POST'])
def upload_students():
    file = request.files.get('excel_file')
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for('students'))

    filename = secure_filename(file.filename)
    save_path = os.path.join(get_uploads_dir(), filename)
    file.save(save_path)

    replace_all = (request.form.get('mode') == 'replace')
    try:
        count = import_students_from_excel(save_path, replace_all=replace_all)
        if count > 0:
            flash(f"Successfully processed {count} students from {filename}!", "success")
        else:
            flash(f"No student records found in {filename}. Please check that the file has columns for Student ID/Adm-No, Student Name, and Class.", "warning")
    except Exception as e:
        flash(f"Error parsing Excel file: {e}", "danger")

    return redirect(url_for('students'))

# ==============================================================================
# ROOMS MANAGER (FULL CRUD)
# ==============================================================================
@app.route('/rooms')
def rooms():
    plan_data = get_seating_plan_data()
    return render_template('rooms.html', rooms=plan_data['rooms_summary'])

@app.route('/rooms/add', methods=['POST'])
def add_room():
    name = request.form.get('name', '').strip()
    block = request.form.get('block', 'Girls Block')
    benches = request.form.get('benches', 20, type=int)
    floor = request.form.get('floor', 'Ground Floor').strip()

    if not name or benches <= 0:
        flash("Valid room name and benches count are required.", "danger")
        return redirect(url_for('rooms'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(print_order) FROM rooms")
    max_ord = cursor.fetchone()[0] or 0

    try:
        cursor.execute('''
        INSERT INTO rooms (name, block, benches, seats_per_bench, floor, print_order, is_active)
        VALUES (?, ?, ?, 2, ?, ?, 1)
        ''', (name, block, benches, floor, max_ord + 1))
        conn.commit()
        flash(f"Room {name} ({benches} benches, {benches*2} seats) created successfully!", "success")
    except Exception as e:
        flash(f"Error creating room: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('rooms'))

@app.route('/rooms/edit/<int:room_id>', methods=['POST'])
def edit_room(room_id):
    name = request.form.get('name', '').strip()
    block = request.form.get('block', 'Girls Block')
    benches = request.form.get('benches', 20, type=int)
    floor = request.form.get('floor', 'Ground Floor').strip()
    print_order = request.form.get('print_order', 1, type=int)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE rooms SET
        name = ?, block = ?, benches = ?, floor = ?, print_order = ?
    WHERE id = ?
    ''', (name, block, benches, floor, print_order, room_id))
    conn.commit()
    conn.close()
    flash("Room settings updated successfully!", "success")
    return redirect(url_for('rooms'))

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()
    flash("Room deleted from system.", "info")
    return redirect(url_for('rooms'))

# ==============================================================================
# ARRANGEMENT GRID (THE CORE ENGINE WORKFLOW)
# ==============================================================================
@app.route('/arrangement')
def arrangement():
    plan_data = get_seating_plan_data()
    conn = get_db()
    cursor = conn.cursor()
    
    # Get list of active rooms for dropdown
    cursor.execute("SELECT name, benches, block FROM rooms WHERE is_active = 1 ORDER BY print_order ASC")
    rooms_list = [dict(r) for r in cursor.fetchall()]

    # Get list of classes and groups for dropdown
    cursor.execute("SELECT DISTINCT class_name FROM students WHERE active = 1 ORDER BY class_name ASC")
    classes = [r['class_name'] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT seating_group FROM students WHERE seating_group != '' AND active = 1 ORDER BY seating_group ASC")
    groups = [r['seating_group'] for r in cursor.fetchall()]

    # Build class stats (count, min_roll, max_roll) for interactive guidance in modal
    cursor.execute("""
        SELECT adm_no, class_name, seating_group, roll_in_class, roll_in_group
        FROM students WHERE active = 1
    """)
    all_std = cursor.fetchall()
    class_stats = {}
    for st in all_std:
        cls = (st['class_name'] or '').strip()
        grp = (st['seating_group'] or '').strip()
        r_cls = st['roll_in_class'] or 1
        r_grp = st['roll_in_group'] or 1

        if cls:
            if cls not in class_stats:
                class_stats[cls] = {'count': 0, 'min_roll': 99999, 'max_roll': 0}
            class_stats[cls]['count'] += 1
            class_stats[cls]['min_roll'] = min(class_stats[cls]['min_roll'], r_cls)
            class_stats[cls]['max_roll'] = max(class_stats[cls]['max_roll'], r_cls)

        if grp:
            if grp not in class_stats:
                class_stats[grp] = {'count': 0, 'min_roll': 99999, 'max_roll': 0}
            class_stats[grp]['count'] += 1
            class_stats[grp]['min_roll'] = min(class_stats[grp]['min_roll'], r_grp)
            class_stats[grp]['max_roll'] = max(class_stats[grp]['max_roll'], r_grp)

    for k, v in class_stats.items():
        if v['min_roll'] == 99999:
            v['min_roll'] = 1

    conn.close()

    room_caps = {
        r['name']: {
            'benches': r['benches'],
            'capacity': r['capacity'],
            'seated': r['seated_count'],
            'free': r['free_seats']
        }
        for r in plan_data['rooms_summary']
    }

    return render_template(
        'arrangement.html',
        arrangements=plan_data['arrangements'],
        rooms=rooms_list,
        classes=classes,
        groups=groups,
        class_stats=class_stats,
        room_caps=room_caps,
        checks=plan_data['system_checks'],
        rooms_summary=plan_data['rooms_summary']
    )

@app.route('/arrangement/add', methods=['POST'])
def add_arrangement():
    room_name = request.form.get('room_name', '').strip()
    class_or_group = request.form.get('class_or_group', '').strip()
    from_roll = request.form.get('from_roll', 1, type=int)
    to_roll = request.form.get('to_roll', 1, type=int)

    if not room_name or not class_or_group or to_roll < from_roll:
        flash("Invalid arrangement block parameters.", "danger")
        return redirect(url_for('arrangement'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(sort_order) FROM arrangements")
    max_ord = cursor.fetchone()[0] or 0

    # Auto-assign row_side if not provided
    row_side = request.form.get('row_side', '').strip().upper()
    if not row_side:
        cursor.execute("SELECT COUNT(*) FROM arrangements WHERE room_name = ?", (room_name,))
        existing_count = cursor.fetchone()[0] or 0
        row_side = 'R' if (existing_count % 2 == 1) else 'L'

    cursor.execute('''
    INSERT INTO arrangements (room_name, row_side, class_or_group, from_roll, to_roll, sort_order)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (room_name, row_side, class_or_group, from_roll, to_roll, max_ord + 1))
    conn.commit()
    conn.close()

    flash(f"Arrangement line added: Room {room_name} - {class_or_group} (Roll {from_roll} to {to_roll})", "success")
    return redirect(url_for('arrangement'))

@app.route('/arrangement/edit/<int:arr_id>', methods=['POST'])
def edit_arrangement(arr_id):
    room_name = request.form.get('room_name', '').strip()
    class_or_group = request.form.get('class_or_group', '').strip()
    from_roll = request.form.get('from_roll', 1, type=int)
    to_roll = request.form.get('to_roll', 1, type=int)

    conn = get_db()
    cursor = conn.cursor()

    row_side = request.form.get('row_side', '').strip().upper()
    if not row_side:
        cursor.execute("SELECT row_side FROM arrangements WHERE id = ?", (arr_id,))
        r = cursor.fetchone()
        row_side = r['row_side'] if r else 'L'

    cursor.execute('''
    UPDATE arrangements SET
        room_name = ?, row_side = ?, class_or_group = ?, from_roll = ?, to_roll = ?
    WHERE id = ?
    ''', (room_name, row_side, class_or_group, from_roll, to_roll, arr_id))
    conn.commit()
    conn.close()

    flash("Arrangement line updated successfully!", "success")
    return redirect(url_for('arrangement'))

@app.route('/arrangement/delete/<int:arr_id>', methods=['POST'])
def delete_arrangement(arr_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM arrangements WHERE id = ?", (arr_id,))
    conn.commit()
    conn.close()
    flash("Arrangement block removed.", "info")
    return redirect(url_for('arrangement'))

@app.route('/arrangement/load-standard-plan', methods=['POST'])
def load_standard_plan():
    from seed_data import DEFAULT_ARRANGEMENTS
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM arrangements")
    for idx, (room, row, cls_grp, f_roll, t_roll) in enumerate(DEFAULT_ARRANGEMENTS):
        cursor.execute('''
        INSERT INTO arrangements (room_name, row_side, class_or_group, from_roll, to_roll, sort_order)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (room, row, cls_grp, f_roll, t_roll, idx + 1))
    conn.commit()
    conn.close()
    flash("Standard School PA-2 Seating Plan loaded! All 16 exam rooms filled to full capacity (480 students allocated).", "success")
    return redirect(url_for('arrangement'))

# ==============================================================================
# HTML PRINT PREVIEW VIEWS
# ==============================================================================
@app.route('/preview/class-plan')
def preview_class_plan():
    plan_data = get_seating_plan_data()
    return render_template('print_class_plan.html', data=plan_data)

@app.route('/preview/room-list')
def preview_room_list():
    plan_data = get_seating_plan_data()
    return render_template('print_room_list.html', data=plan_data)

@app.route('/preview/attendance')
def preview_attendance():
    plan_data = get_seating_plan_data()
    return render_template('print_attendance.html', data=plan_data)

@app.route('/preview/master-summary')
def preview_master_summary():
    plan_data = get_seating_plan_data()
    return render_template('print_master_summary.html', data=plan_data)

@app.route('/preview/consolidated-sheet')
def preview_consolidated_sheet():
    cons_data = get_consolidated_sheet_data()
    return render_template('print_consolidated.html', data=cons_data)

# ==============================================================================
# DOWNLOADS & EXPORTS (WORD .DOCX + EXCEL .XLSX)
# ==============================================================================
@app.route('/export/class-plan.docx')
def export_class_plan_docx():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Class_Seating_Arrangement_Plan_PA2.docx')
    generate_class_plan_docx(file_path)
    return send_file(file_path, as_attachment=True, download_name='Class_Seating_Arrangement_Plan_PA2.docx')

@app.route('/export/room-list.docx')
def export_room_list_docx():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Roomwise_Notice_Board_List_PA2.docx')
    generate_roomwise_display_docx(file_path)
    return send_file(file_path, as_attachment=True, download_name='Roomwise_Notice_Board_List_PA2.docx')

@app.route('/export/attendance.docx')
def export_attendance_docx():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Exam_Attendance_Sheet_PA2.docx')
    generate_attendance_sheet_docx(file_path)
    return send_file(file_path, as_attachment=True, download_name='Exam_Attendance_Sheet_PA2.docx')

@app.route('/export/master-summary.docx')
def export_master_summary_docx():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Master_Seating_Arrangements_Summary_PA2.docx')
    generate_master_summary_docx(file_path)
    return send_file(file_path, as_attachment=True, download_name='Master_Seating_Arrangements_Summary_PA2.docx')

@app.route('/export/master-excel.xlsx')
def export_master_excel():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Master_Seating_Arrangement_Consolidated.xlsx')
    generate_master_excel(file_path)
    return send_file(file_path, as_attachment=True, download_name='Master_Seating_Arrangement_Consolidated.xlsx')

@app.route('/export/consolidated-sheet.xlsx')
def export_consolidated_excel():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Consolidated_Marks_Sheet_PA2.xlsx')
    generate_consolidated_excel(file_path)
    return send_file(file_path, as_attachment=True, download_name='Consolidated_Marks_Sheet_PA2.xlsx')

@app.route('/export/consolidated-sheet.docx')
def export_consolidated_docx():
    exports_dir = get_exports_dir()
    file_path = os.path.join(exports_dir, 'Consolidated_Marks_Sheet_PA2.docx')
    generate_consolidated_docx(file_path)
    return send_file(file_path, as_attachment=True, download_name='Consolidated_Marks_Sheet_PA2.docx')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
