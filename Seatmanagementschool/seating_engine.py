import json
import re
from collections import defaultdict
from database import get_db

ROMAN_NUMERALS = {
    '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V',
    '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X',
    '11': 'XI', '12': 'XII'
}

def to_roman_class(class_name):
    """
    Converts '6 A' -> 'VI-A', '10 D' -> 'X-D', '11' -> 'XI', '6 HIFZ' -> 'VI HIFZ'
    """
    parts = class_name.strip().split()
    if not parts:
        return class_name
    grade = parts[0]
    roman_grade = ROMAN_NUMERALS.get(grade, grade)
    if len(parts) > 1:
        sec = parts[1]
        if len(sec) == 1 and sec.isalpha():
            return f"{roman_grade}-{sec}"
        return f"{roman_grade} {sec}"
    return roman_grade

def get_seating_plan_data():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Fetch Settings
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    try:
        attendance_dates = json.loads(settings.get('attendance_dates_json', '[]'))
    except Exception:
        attendance_dates = []

    # Format dates nicely (e.g. 16/11) for web and docx previews
    for dt in attendance_dates:
        raw_d = dt.get('date', '').strip()
        if '-' in raw_d and len(raw_d) == 10:
            parts = raw_d.split('-')
            dt['date'] = f"{parts[2]}/{parts[1]}"
            dt['date_full'] = f"{parts[2]}/{parts[1]}/{parts[0]}"

    # 2. Fetch Rooms ordered by print_order
    cursor.execute("SELECT * FROM rooms WHERE is_active = 1 ORDER BY print_order ASC, id ASC")
    rooms_rows = [dict(r) for r in cursor.fetchall()]

    # 3. Fetch Arrangements ordered by sort_order
    cursor.execute("SELECT * FROM arrangements ORDER BY sort_order ASC, id ASC")
    arrangement_rows = [dict(r) for r in cursor.fetchall()]

    # 4. Fetch Students
    cursor.execute("SELECT * FROM students WHERE active = 1 ORDER BY class_name ASC, roll_in_class ASC, adm_no ASC")
    student_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Build student lookups
    # Map by adm_no
    students_by_adm = {s['adm_no']: dict(s) for s in student_rows}
    
    # Map by (used_group, roll_in_group)
    # used_group is seating_group if non-empty, else class_name
    students_by_group_roll = {}
    students_by_class_roll = {}
    group_students_list = defaultdict(list)
    class_students_list = defaultdict(list)

    for s in student_rows:
        used_grp = s['seating_group'] if s.get('seating_group') else s['class_name']
        s['used_group'] = used_grp
        r_grp = s.get('roll_in_group') or 0
        r_cls = s.get('roll_in_class') or 0
        
        students_by_group_roll[(used_grp, r_grp)] = s
        students_by_class_roll[(s['class_name'], r_cls)] = s

        # Clean variants (e.g. '7 HIFZ2', '7 HIFZ (2' -> '7 HIFZ')
        clean_cls = re.sub(r'[\(\)\[\]]', '', s['class_name'])
        clean_cls = re.sub(r'(HIFZ)\s*\d*$', r'\1', clean_cls, flags=re.IGNORECASE).strip()
        clean_cls = re.sub(r'\s+', ' ', clean_cls)
        if clean_cls:
            students_by_class_roll[(clean_cls, r_cls)] = s
            if not s.get('seating_group'):
                students_by_group_roll[(clean_cls, r_grp)] = s

        group_students_list[used_grp].append(s)
        class_students_list[s['class_name']].append(s)

    # 5. Process Arrangement Blocks
    student_allotment = {} # adm_no -> {'room': room_name, 'row': row_side, 'pos': position}
    placement_counts = defaultdict(int) # adm_no -> count
    
    room_allocations = {}
    for rm in rooms_rows:
        rname = rm['name']
        room_allocations[rname] = {
            'info': rm,
            'name': rname,
            'benches': rm['benches'],
            'capacity': rm['benches'] * rm.get('seats_per_bench', 2),
            'block': rm['block'],
            'left_students': [],
            'right_students': [],
            'all_students': []
        }

    plan_disagreements = []

    for arr in arrangement_rows:
        rname = arr['room_name']
        rside = arr['row_side']
        cls_grp = arr['class_or_group'].strip()
        f_roll = arr['from_roll']
        t_roll = arr['to_roll']
        expected_count = t_roll - f_roll + 1

        matched_in_slice = []
        for r_num in range(f_roll, t_roll + 1):
            st = students_by_group_roll.get((cls_grp, r_num))
            if not st:
                # Fallback to class roll
                st = students_by_class_roll.get((cls_grp, r_num))
            if not st:
                clean_target = re.sub(r'[\(\)\[\]]', '', cls_grp)
                clean_target = re.sub(r'(HIFZ)\s*\d*$', r'\1', clean_target, flags=re.IGNORECASE).strip()
                clean_target = re.sub(r'\s+', ' ', clean_target)
                st = students_by_group_roll.get((clean_target, r_num)) or students_by_class_roll.get((clean_target, r_num))
                
            if st:
                matched_in_slice.append(st)
                adm = st['adm_no']
                placement_counts[adm] += 1
                
                # Assign to room
                st_info = {
                    'adm_no': adm,
                    'name': st['name'],
                    'class_name': st['class_name'],
                    'seating_group': st.get('seating_group', ''),
                    'roll_in_group': st.get('roll_in_group', 0),
                    'roll_in_class': st.get('roll_in_class', 0),
                    'room_name': rname,
                    'row_side': rside,
                    'gender': st.get('gender', 'M'),
                    'block': st.get('block', 'Boys Block'),
                    'is_hifz': st.get('is_hifz', 0),
                    'is_hindi': st.get('is_hindi', 0)
                }
                student_allotment[adm] = st_info

                if rname in room_allocations:
                    if rside == 'L':
                        room_allocations[rname]['left_students'].append(st_info)
                    else:
                        room_allocations[rname]['right_students'].append(st_info)
                    room_allocations[rname]['all_students'].append(st_info)

        actual_count = len(matched_in_slice)
        arr['count'] = actual_count
        arr['expected_count'] = expected_count
        arr['found_count'] = actual_count
        arr['status'] = 'MATCH' if actual_count == expected_count else 'MISMATCH'
        arr['status_detail'] = f"Expected {expected_count}, found {actual_count}"
        arr['students'] = matched_in_slice

        if actual_count != expected_count:
            plan_disagreements.append({
                'arrangement': arr,
                'expected': expected_count,
                'found': actual_count,
                'message': f"Line {arr['id']} (Room {rname} &bull; {cls_grp} Rolls {f_roll}-{t_roll}): Entered {expected_count} roll slots, but only {actual_count} student(s) found in database."
            })

    # 6. Build Room Summary Stats
    rooms_summary = []
    rooms_over_capacity = []

    for rm in rooms_rows:
        rname = rm['name']
        alloc = room_allocations.get(rname, {
            'info': rm, 'name': rname, 'benches': rm['benches'],
            'capacity': rm['benches'] * 2, 'block': rm['block'],
            'left_students': [], 'right_students': [], 'all_students': []
        })
        left_cnt = len(alloc['left_students'])
        right_cnt = len(alloc['right_students'])
        tot_cnt = left_cnt + right_cnt
        cap = alloc['capacity']
        is_over = tot_cnt > cap

        # Summarize class text for display (unified without left/right rows)
        all_grp_map = defaultdict(list)
        for st in alloc['all_students']:
            all_grp_map[st['seating_group'] or st['class_name']].append(st['roll_in_group'] or st['roll_in_class'])
        allotted_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in all_grp_map.items()])

        left_grp_map = defaultdict(list)
        for st in alloc['left_students']:
            left_grp_map[st['seating_group'] or st['class_name']].append(st['roll_in_group'] or st['roll_in_class'])
        left_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in left_grp_map.items()])

        right_grp_map = defaultdict(list)
        for st in alloc['right_students']:
            right_grp_map[st['seating_group'] or st['class_name']].append(st['roll_in_group'] or st['roll_in_class'])
        right_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in right_grp_map.items()])

        # Sort all students alphabetically by candidate name (Name-wise order)
        all_std_sorted = sorted(alloc['all_students'], key=lambda s: (s.get('name') or '').strip().upper())

        summary_item = {
            'id': rm.get('id', 0),
            'name': rname,
            'block': rm['block'],
            'benches': rm['benches'],
            'capacity': cap,
            'floor': rm.get('floor', 'Ground Floor'),
            'print_order': rm.get('print_order', 1),
            'allotted_classes_text': allotted_txt,
            'left_count': left_cnt,
            'right_count': right_cnt,
            'left_class_text': left_txt,
            'right_class_text': right_txt,
            'total_seated': tot_cnt,
            'seated_count': tot_cnt,
            'free_seats': max(0, cap - tot_cnt),
            'left_students': alloc['left_students'],
            'right_students': alloc['right_students'],
            'all_students': all_std_sorted,
            'name_sorted_students': all_std_sorted,
            'is_over_capacity': is_over,
            'status': 'OK' if not is_over else f'OVER ({tot_cnt}/{cap})'
        }
        rooms_summary.append(summary_item)
        if is_over:
            rooms_over_capacity.append(summary_item)

    # 7. Build Class Plan (Class by class view)
    class_order_setting = settings.get('class_print_order', 'Section first')
    distinct_classes = sorted(list(class_students_list.keys()))

    def class_sort_key(cname):
        parts = cname.split()
        gr = parts[0]
        sec = parts[1] if len(parts) > 1 else ''
        try:
            gr_num = int(gr)
        except ValueError:
            gr_num = 99
        if class_order_setting == 'Section first':
            return (sec, gr_num)
        return (gr_num, sec)

    ordered_classes = sorted(distinct_classes, key=class_sort_key)
    
    classes_plan_data = []
    for cls in ordered_classes:
        c_students = class_students_list[cls]
        c_plan_students = []
        # Find which arrangement lines cover this class
        allotments_for_class = []
        for arr in arrangement_rows:
            if arr['class_or_group'] == cls:
                allotments_for_class.append({
                    'room_name': arr['room_name'],
                    'row_side': arr['row_side'],
                    'from_roll': arr['from_roll'],
                    'to_roll': arr['to_roll'],
                    'count': arr['to_roll'] - arr['from_roll'] + 1
                })

        for st in c_students:
            adm = st['adm_no']
            allot = student_allotment.get(adm, {})
            room_allotted = allot.get('room_name', 'NOT ALLOTTED')
            c_plan_students.append({
                'adm_no': adm,
                'name': st['name'],
                'gender': st.get('gender', 'M'),
                'roll_no': st.get('roll_in_class') or 0,
                'roll_in_class': st.get('roll_in_class') or 0,
                'roll_in_group': st.get('roll_in_group') or 0,
                'room_allotted': room_allotted,
                'allotted_room': room_allotted,
                'row_side': allot.get('row_side', '')
            })
        classes_plan_data.append({
            'class_name': cls,
            'display_name': to_roman_class(cls),
            'students': c_plan_students,
            'total_students': len(c_plan_students),
            'total_strength': len(c_plan_students),
            'allotments': allotments_for_class
        })

    # 8. Compute System Integrity Checks
    unseated_students = [s for s in student_rows if s['adm_no'] not in student_allotment]
    placed_twice = [adm for adm, cnt in placement_counts.items() if cnt > 1]

    system_checks = {
        'students_loaded': len(student_rows),
        'total_students_loaded': len(student_rows),
        'classes_found': len(distinct_classes),
        'rooms_in_use': sum(1 for rm in rooms_summary if rm['total_seated'] > 0),
        'total_rooms': len(rooms_rows),
        'students_unseated': len(unseated_students),
        'unseated_count': len(unseated_students),
        'students_placed_twice': len(placed_twice),
        'duplicate_count': len(placed_twice),
        'plan_disagreements': len(plan_disagreements),
        'disagreement_count': len(plan_disagreements),
        'rooms_over_capacity': len(rooms_over_capacity),
        'over_capacity_count': len(rooms_over_capacity),
        'all_ok': (len(unseated_students) == 0 and len(placed_twice) == 0 and len(plan_disagreements) == 0 and len(rooms_over_capacity) == 0),
        'all_checks_pass': (len(unseated_students) == 0 and len(placed_twice) == 0 and len(plan_disagreements) == 0 and len(rooms_over_capacity) == 0),
        'unseated_list': unseated_students,
        'placed_twice_list': placed_twice,
        'disagreements_list': plan_disagreements,
        'over_capacity_rooms': [r['name'] for r in rooms_over_capacity]
    }

    return {
        'settings': settings,
        'attendance_dates': attendance_dates,
        'rooms_summary': rooms_summary,
        'classes_plan': classes_plan_data,
        'system_checks': system_checks,
        'all_students': student_rows,
        'arrangements': arrangement_rows
    }

if __name__ == '__main__':
    data = get_seating_plan_data()
    checks = data['system_checks']
    print("=" * 60)
    print("SYSTEM HEALTH CHECKS:")
    print(f"Students Loaded: {checks['students_loaded']}")
    print(f"Classes Found: {checks['classes_found']}")
    print(f"Rooms in Use: {checks['rooms_in_use']} / {checks['total_rooms']}")
    print(f"Students Unseated: {checks['students_unseated']}")
    print(f"Students Placed Twice: {checks['students_placed_twice']}")
    print(f"Plan Disagreements: {checks['plan_disagreements']}")
    print(f"Rooms Over Capacity: {checks['rooms_over_capacity']}")
    print(f"All Checks Pass: {checks['all_ok']}")
    if checks['disagreements_list']:
        print("Disagreements detail:")
        for d in checks['disagreements_list']:
            print(" ", d['message'])
