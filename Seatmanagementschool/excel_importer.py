import os
import openpyxl
import csv
import re
from database import get_db

GIRLS_11_12_ADM = {
    'CIS1960', # MISBAH FATIMA (11 ACC)
    'CIS1986', 'CIS2028', # ZOHA SIDDIQUI, ZOYA JABEEN (11 PCB)
    'CIS0848', 'CIS1316', # AYESHA JAHAN, HUDA TAZMEEN (11 PCM)
    'CIS1885', 'CIS1822', 'CIS1824', 'CIS1854', 'CIS1906', 'CIS1835', 'CIS1836', # 12 ACC
    'CIS1864', 'CIS1867', 'CIS1874', 'CIS1872', 'CIS1879', 'CIS1816', # 12 PCB
    'CIS1865', # ZUBIYAH MARYAM (12 PCM)
}

FEMALE_KEYWORDS = [
    'FATIMA', 'FATHIMA', 'MARYAM', 'JABEEN', 'SIDDIQUI', 'JAHAN', 'TAZMEEN', 'SAIF',
    'QUADRI', 'BEGUM', 'UNNISA', 'ASKARI', 'KULSUM', 'AAREEBA', 'AREEBA', 'KHADEEJA',
    'MANAHIL', 'KULSOOM', 'SUMAIYA', 'UMAMAH', 'ZUBIYAH', 'HURIYA', 'IFRA', 'LUBNA',
    'MAIRA', 'SOFIA', 'AASIYA', 'ZOHA', 'ZOYA', 'HUDA', 'AYESHA', 'MISBAH', 'BEGUM',
    'SYEDA', 'KHATOON', 'ANJUM', 'NAAZ', 'TABASSUM'
]

HINDI_STUDENTS_NAMES = {
    'UZMA NAAZ', 'NAMEERA NAVEED', 'SHEEMA IFFAT', 'AFIA MAHSHAR',
    'BILAL MUDASSIR', 'ARSALAN SADIQ', 'ABDUL RAHMAN', 'SALEH BIN SULTAN', 'HASHIR',
    'ZAHRA FATIMA', 'HARMAIN FATIMA', 'AYAAN BASHADI', 'SYED OMAR FAROOQ',
    'AFIA FAROOQ', 'AYESHA HUMERA', 'MADEEHA MIRZA', 'SYEDA RUMAISA', 'SYEDA RUQYA ABBASI',
    'SYEDA TASNEEM FATIMA', 'ZAREEN RUQAIYA', 'ZAINAB ALI', 'BARAKAH SHAHID', 'ZOBIA SIDDIQUI',
    'ADEEB SHAHERYAR', 'HASSAN SALIM', 'MD ALHAAN SADEED', 'ADEEBA MIRZA',
    'MD ABDULLAH', 'AMMED RAZA', 'MUAZZIN HUSSAIN', 'AHMED HUSSAINI', 'MOHD RAYYAN', 'AMEERUDDIN HAMZA',
    'AFSHEEN PARVEEN', 'NIDA NAVEED', 'AFIA BEGUM', 'SOFIA SK.', 'SUMAIYYA F', 'SAFA SULTANA',
    'AYESHA SAHIL', 'ZAINAB KAUSAR', 'SANOBER', 'MARYAM TASLEEM', 'FATIMA ZAHRA', 'MUBASHIRA ANJUM',
    'MD FARHAN', 'SAYEED AHMED', 'SAFIUDDIN ZAIN', 'MOMIN OMAR', 'JUNAID', 'AIDAN', 'MUSAB', 'MAAZ', 'MUSTAFA HUSSAIN'
}

def normalize_student_record(raw_class, adm, name, raw_group=None, raw_gender=None, raw_block=None):
    """
    Normalizes class name, seating group, gender, block, and exemptions.
    """
    cls = re.sub(r'\s+', ' ', str(raw_class or '').strip())
    raw_name = str(name or '').strip()
    clean_name = raw_name.upper().replace('.', ' ').strip()
    adm_clean = str(adm or '').strip().upper()
    stream = ''
    seating_group = str(raw_group or '').strip()
    is_hifz = 0

    # 1. Hifz detection
    if 'HIFZ' in cls.upper():
        m = re.search(r'(\d+)', cls)
        g_num = m.group(1) if m else '6'
        norm_class = f"{g_num} HIFZ"
        gender = 'M'
        block = 'Boys Block'
        is_hifz = 1

    # 2. Senior secondary 11 & 12
    elif re.search(r'\b(11|12)\b', cls):
        g_num = '11' if '11' in cls else '12'
        norm_class = g_num
        st_match = re.search(r'(ACCOUNTANCY|PCB|PCM)', cls, re.IGNORECASE)
        if st_match:
            stream = st_match.group(1).upper()

        if not raw_gender:
            is_female = (adm_clean in GIRLS_11_12_ADM) or any(k in clean_name for k in FEMALE_KEYWORDS)
            gender = 'F' if is_female else 'M'
        else:
            gender = 'F' if str(raw_gender).strip().upper().startswith('F') else 'M'

        block = 'Girls Block' if gender == 'F' else 'Boys Block'

        if not seating_group:
            seating_group = f"{g_num} G" if gender == 'F' else f"{g_num} B"

    # 3. Standard classes (6 A, 7 B, 10 D, etc.)
    else:
        m = re.search(r'(\d+)\s*([A-Za-z]+)', cls)
        if m:
            g_num = m.group(1)
            sec = m.group(2).upper()
            norm_class = f"{g_num} {sec}"
        else:
            norm_class = cls.upper()

        if not raw_gender:
            # Crescent School rules: 'A' sections and '10 D' are Girls; 'B', 'C' sections are Boys
            is_female = ('A' in norm_class and 'HIFZ' not in norm_class) or ('10 D' in norm_class)
            gender = 'F' if is_female else 'M'
        else:
            gender = 'F' if str(raw_gender).strip().upper().startswith('F') else 'M'

        block = raw_block if raw_block else ('Girls Block' if gender == 'F' else 'Boys Block')

    # Hindi exemption check
    is_hindi = 1 if any(hn in clean_name for hn in HINDI_STUDENTS_NAMES) else 0

    return {
        'adm_no': adm_clean,
        'name': raw_name,
        'class_name': norm_class,
        'seating_group': seating_group,
        'stream': stream,
        'gender': gender,
        'block': block,
        'is_hifz': is_hifz,
        'is_hindi': is_hindi
    }

def detect_columns(rows):
    """
    Detects column mapping (adm, name, class, group, gender, block)
    from a list of row tuples (first 10 rows).
    Returns (header_row_idx, col_map) where col_map is dict of col_name -> col_idx.
    """
    col_map = {}
    header_row_idx = None

    # Try matching header row
    for r_idx, row in enumerate(rows[:10]):
        temp_map = {}
        for c_idx, val in enumerate(row):
            if val is None:
                continue
            h = str(val).strip().lower()
            if not h:
                continue

            # Admission No column
            if ('adm' in h or 'admission' in h or 'reg' in h or h == 'id' or 'student id' in h or 'roll' in h) and 'class' not in h:
                temp_map['adm'] = c_idx
            # Class column
            elif 'class' in h or 'grade' in h or 'standard' in h or 'sec' in h:
                temp_map['class'] = c_idx
            # Student Name column
            elif 'name' in h or 'student' in h or 'candidate' in h:
                temp_map['name'] = c_idx
            # Seating Group column
            elif 'group' in h or 'seating' in h:
                temp_map['group'] = c_idx
            # Gender column
            elif 'gender' in h or 'sex' in h:
                temp_map['gender'] = c_idx
            # Block column
            elif 'block' in h or 'wing' in h:
                temp_map['block'] = c_idx

        # If at least 2 key columns found, this is the header row
        if len(temp_map) >= 2 and ('adm' in temp_map or 'name' in temp_map or 'class' in temp_map):
            col_map = temp_map
            header_row_idx = r_idx
            break

    # If no explicit header row found, infer columns from data patterns
    if not col_map or 'adm' not in col_map or 'name' not in col_map:
        for r_idx, row in enumerate(rows[:5]):
            for c_idx, val in enumerate(row):
                if val is None:
                    continue
                v = str(val).strip()
                if not v:
                    continue
                # Adm pattern (e.g. CIS1234 or numbers)
                if re.match(r'^(CIS\d+|\d{3,6})$', v, re.IGNORECASE) and 'adm' not in col_map:
                    col_map['adm'] = c_idx
                # Class pattern (e.g. 6 A, 10 B, 11 PCM, 6 ( Hifz))
                elif re.match(r'^\s*(\d{1,2}\s*[A-Za-z]+|\d{1,2}\s*\(.*\)|HIFZ)', v, re.IGNORECASE) and 'class' not in col_map:
                    col_map['class'] = c_idx
                # Name pattern (letters and spaces, at least 4 chars)
                elif re.match(r'^[A-Za-z\s\.\']{4,}$', v) and 'name' not in col_map and c_idx != col_map.get('class'):
                    col_map['name'] = c_idx

        if header_row_idx is None:
            header_row_idx = -1  # Data starts at row 0

    return header_row_idx, col_map

def import_students_from_excel(filepath, replace_all=True):
    """
    Dynamically imports students from any Excel (.xlsx, .xls) or CSV file.
    Supports:
    1. Dynamic Report flat sheets (e.g. Dynamic_Report.xlsx: Student Adm-No, Student First Name, Class Name)
    2. Official Template sheets (Class, Admission No, Student Name, Seating Group)
    3. Legacy Multi-tab school consolidated marksheet (GR 6A, GR 6B, GR 11, etc.)
    4. Arbitrary CSV / Excel exports with intelligent header detection
    """
    records = []
    class_counters = {}
    group_counters = {}

    is_csv = filepath.lower().endswith('.csv')

    if is_csv:
        rows = []
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    reader = csv.reader(f)
                    rows = [r for r in reader]
                break
            except Exception:
                continue

        if not rows:
            return 0

        header_idx, col_map = detect_columns(rows)
        start_row = 0 if header_idx is None else header_idx + 1

        for row in rows[start_row:]:
            if not row or not any(row):
                continue
            adm_val = row[col_map['adm']] if 'adm' in col_map and col_map['adm'] < len(row) else ''
            name_val = row[col_map['name']] if 'name' in col_map and col_map['name'] < len(row) else ''
            class_val = row[col_map['class']] if 'class' in col_map and col_map['class'] < len(row) else ''
            group_val = row[col_map['group']] if 'group' in col_map and col_map['group'] < len(row) else ''
            gender_val = row[col_map['gender']] if 'gender' in col_map and col_map['gender'] < len(row) else ''
            block_val = row[col_map['block']] if 'block' in col_map and col_map['block'] < len(row) else ''

            if not adm_val and not name_val:
                continue

            rec = normalize_student_record(class_val, adm_val, name_val, group_val, gender_val, block_val)
            cls_name = rec['class_name']
            seating_grp = rec['seating_group']

            class_counters[cls_name] = class_counters.get(cls_name, 0) + 1
            rec['roll_in_class'] = class_counters[cls_name]

            used_grp = seating_grp if seating_grp else cls_name
            group_counters[used_grp] = group_counters.get(used_grp, 0) + 1
            rec['roll_in_group'] = group_counters[used_grp]

            records.append(rec)

    else:
        # Excel .xlsx / .xls file
        wb = openpyxl.load_workbook(filepath, data_only=True)

        # Check for multi-tab format (e.g. GR 6A, GR 6B, GR 11, etc.)
        multi_tab_classes = [
            s for s in wb.sheetnames
            if any(p in s.upper() for p in ['GR 6', 'GR 7', 'GR 8', 'GR 9', 'GR 10', 'GR 11', 'GR 12', 'GRADE 6', 'GRADE 11'])
        ]

        if multi_tab_classes and len(multi_tab_classes) > 2:
            # Multi-tab legacy parser
            for sname in wb.sheetnames:
                clean_sname = sname.strip()
                if clean_sname.lower() in ['sheet14', 'summary', 'blank', 'start here', 'settings']:
                    continue
                ws = wb[sname]

                # Senior secondary sheets
                if any(x in clean_sname.upper() for x in ['GR 11', 'GR 12', 'GRADE 11', 'GRADE 12']):
                    grade_num = "11" if '11' in clean_sname else "12"
                    for r in range(1, ws.max_row + 1):
                        sno = ws.cell(r, 1).value
                        adm = str(ws.cell(r, 2).value or '').strip()
                        name = str(ws.cell(r, 3).value or '').strip()

                        if sno and str(sno).isdigit() and adm.upper().startswith('CIS'):
                            rec = normalize_student_record(grade_num, adm, name)
                            cls_name = rec['class_name']
                            seating_grp = rec['seating_group']

                            class_counters[cls_name] = class_counters.get(cls_name, 0) + 1
                            rec['roll_in_class'] = class_counters[cls_name]

                            used_grp = seating_grp if seating_grp else cls_name
                            group_counters[used_grp] = group_counters.get(used_grp, 0) + 1
                            rec['roll_in_group'] = group_counters[used_grp]

                            records.append(rec)
                    continue

                # Standard grade tab e.g. "GR 6A", "GR 6B", "GR 6 HIFZ", "GR 10  A "
                m = re.search(r'GR\s*(\d+)\s*([A-Za-z]+(?:\s+HIFZ|\s+[A-Za-z0-9\(\)]+)?)', clean_sname, re.IGNORECASE)
                if not m:
                    m = re.search(r'(\d+)\s*([A-Za-z]+)', clean_sname, re.IGNORECASE)

                if m:
                    gr_num = m.group(1).strip()
                    raw_sec = m.group(2)
                    raw_sec = re.sub(r'\s*[\(\[].*?[\)\]]?', '', raw_sec)
                    sec_part = re.sub(r'[^\w\s]', '', raw_sec).strip().upper()
                    tab_class = f"{gr_num} {sec_part}".strip()
                else:
                    tab_class = re.sub(r'\s*[\(\[].*?[\)\]]?', '', clean_sname).strip().upper()

                for r in range(1, ws.max_row + 1):
                    sno = ws.cell(r, 1).value
                    adm = str(ws.cell(r, 2).value or '').strip()
                    name = str(ws.cell(r, 3).value or '').strip()

                    if sno and str(sno).isdigit() and adm.upper().startswith('CIS'):
                        rec = normalize_student_record(tab_class, adm, name)
                        cls_name = rec['class_name']
                        seating_grp = rec['seating_group']

                        class_counters[cls_name] = class_counters.get(cls_name, 0) + 1
                        rec['roll_in_class'] = class_counters[cls_name]

                        used_grp = seating_grp if seating_grp else cls_name
                        group_counters[used_grp] = group_counters.get(used_grp, 0) + 1
                        rec['roll_in_group'] = group_counters[used_grp]

                        records.append(rec)

        else:
            # Single/flat sheet (Dynamic Report, PA2_Seating_Simple, Student_Import_Template, etc.)
            target_sheet = None
            if 'Students' in wb.sheetnames:
                target_sheet = wb['Students']
            elif 'Sheet' in wb.sheetnames:
                target_sheet = wb['Sheet']
            elif 'Sheet1' in wb.sheetnames:
                target_sheet = wb['Sheet1']
            else:
                target_sheet = wb.active

            rows = list(target_sheet.iter_rows(values_only=True))
            if not rows:
                return 0

            header_idx, col_map = detect_columns(rows)
            start_row = 0 if header_idx is None else header_idx + 1

            for row in rows[start_row:]:
                if not row or not any(row):
                    continue

                adm_val = row[col_map['adm']] if 'adm' in col_map and col_map['adm'] < len(row) else ''
                name_val = row[col_map['name']] if 'name' in col_map and col_map['name'] < len(row) else ''
                class_val = row[col_map['class']] if 'class' in col_map and col_map['class'] < len(row) else ''
                group_val = row[col_map['group']] if 'group' in col_map and col_map['group'] < len(row) else ''
                gender_val = row[col_map['gender']] if 'gender' in col_map and col_map['gender'] < len(row) else ''
                block_val = row[col_map['block']] if 'block' in col_map and col_map['block'] < len(row) else ''

                # Skip header repetitions or empty rows
                if not adm_val and not name_val:
                    continue
                if str(adm_val).strip().lower() in ['adm', 'admission', 'student adm-no', 'adm no']:
                    continue

                rec = normalize_student_record(class_val, adm_val, name_val, group_val, gender_val, block_val)
                cls_name = rec['class_name']
                seating_grp = rec['seating_group']

                class_counters[cls_name] = class_counters.get(cls_name, 0) + 1
                rec['roll_in_class'] = class_counters[cls_name]

                used_grp = seating_grp if seating_grp else cls_name
                group_counters[used_grp] = group_counters.get(used_grp, 0) + 1
                rec['roll_in_group'] = group_counters[used_grp]

                records.append(rec)

    if not records:
        return 0

    conn = get_db()
    cursor = conn.cursor()

    if replace_all:
        cursor.execute("DELETE FROM students")

    for rec in records:
        cursor.execute('''
        INSERT INTO students (
            adm_no, name, class_name, seating_group, stream, gender, block,
            roll_in_group, roll_in_class, is_hifz, is_hindi, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(adm_no) DO UPDATE SET
            name = excluded.name,
            class_name = excluded.class_name,
            seating_group = excluded.seating_group,
            stream = excluded.stream,
            gender = excluded.gender,
            block = excluded.block,
            roll_in_group = excluded.roll_in_group,
            roll_in_class = excluded.roll_in_class,
            is_hifz = excluded.is_hifz,
            is_hindi = excluded.is_hindi,
            active = 1
        ''', (
            rec['adm_no'], rec['name'], rec['class_name'], rec['seating_group'],
            rec.get('stream', ''), rec['gender'], rec['block'],
            rec['roll_in_group'], rec['roll_in_class'],
            rec['is_hifz'], rec['is_hindi']
        ))

    conn.commit()
    conn.close()
    return len(records)
