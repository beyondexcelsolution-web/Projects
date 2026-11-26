import os
from collections import defaultdict
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from seating_engine import get_seating_plan_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, 'static', 'images', 'school_logo.png')
BANNER_WIDE_PATH = os.path.join(BASE_DIR, 'static', 'images', 'school_banner_wide.png')
BANNER_MED_PATH = os.path.join(BASE_DIR, 'static', 'images', 'school_banner_medium.png')

def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn('w:{}'.format(key)), str(val))

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def make_table_header_repeat(table, header_rows_count=1):
    for r_i in range(min(header_rows_count, len(table.rows))):
        trPr = table.rows[r_i]._tr.get_or_add_trPr()
        trPr.append(OxmlElement('w:tblHeader'))

def add_horizontal_straight_line(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')  # 1.5 pt solid line
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    p._p.get_or_add_pPr().append(pBdr)

def add_header_banner(doc, banner_type='wide'):
    path = BANNER_WIDE_PATH if banner_type == 'wide' else BANNER_MED_PATH
    if os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run()
        # Full printable width (A4 portrait width 8.27in - 2*0.5in margins = 7.27in)
        width = Inches(7.27)
        run.add_picture(path, width=width)
    elif os.path.exists(LOGO_PATH):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run()
        run.add_picture(LOGO_PATH, width=Inches(1.2))

# ==============================================================================
# 1. CLASS PLAN DOCX (PA1 SEATING ARRANGEMENT PLAN 26-27.docx)
# ==============================================================================
def generate_class_plan_docx(output_path):
    data = get_seating_plan_data()
    settings = data['settings']
    classes_plan = data['classes_plan']
    
    exam_title = settings.get('exam_title', 'Periodic Assessment – 2')
    acad_year = settings.get('academic_year', '2026-27')

    doc = docx.Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.4)
        sec.bottom_margin = Inches(0.4)
        sec.left_margin = Inches(0.5)
        sec.right_margin = Inches(0.5)

    CHUNK_SIZE = 26
    is_first_page = True

    for c_data in classes_plan:
        students = c_data['students']
        chunks = [students[i:i + CHUNK_SIZE] for i in range(0, len(students), CHUNK_SIZE)] or [[]]

        for p_idx, chunk in enumerate(chunks):
            if not is_first_page:
                doc.add_page_break()
            is_first_page = False

            add_header_banner(doc, banner_type='wide')

            # Title
            p_title = doc.add_paragraph()
            p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_title.paragraph_format.space_before = Pt(2)
            p_title.paragraph_format.space_after = Pt(1)
            r_t = p_title.add_run(f"{exam_title}, ({acad_year})\nSeating Arrangements")
            r_t.font.name = 'Times New Roman'
            r_t.font.size = Pt(12)
            r_t.font.bold = True

            # Class line
            p_cls = doc.add_paragraph()
            p_cls.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_cls.paragraph_format.space_before = Pt(2)
            p_cls.paragraph_format.space_after = Pt(4)
            page_suffix = f" (Page {p_idx+1})" if len(chunks) > 1 else ""
            r_c = p_cls.add_run(f"CLASS:  {c_data['display_name']}{page_suffix}\t\t\tName List\t\t\tClass Tr.__________")
            r_c.font.name = 'Times New Roman'
            r_c.font.size = Pt(10.5)
            r_c.font.bold = True

            add_horizontal_straight_line(doc)

            # Table
            table = doc.add_table(rows=len(chunk) + 1, cols=4)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            make_table_header_repeat(table, 1)

            headers = ['S.NO', 'Registration No.', 'NAME OF THE STUDENT', 'CLASS ALLOTTED']
            col_widths = [Inches(0.6), Inches(1.5), Inches(3.4), Inches(1.8)]

            hdr_row = table.rows[0]
            for c_idx, h_text in enumerate(headers):
                cell = hdr_row.cells[c_idx]
                cell.width = col_widths[c_idx]
                cell.text = h_text
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.runs[0].font.name = 'Times New Roman'
                p.runs[0].font.size = Pt(9.5)
                p.runs[0].font.bold = True
                set_cell_background(cell, 'F1F5F9')
                set_cell_border(cell, top={"sz": 4, "val": "single", "color": "000000"},
                                      bottom={"sz": 4, "val": "single", "color": "000000"},
                                      left={"sz": 4, "val": "single", "color": "000000"},
                                      right={"sz": 4, "val": "single", "color": "000000"})

            for r_i, st in enumerate(chunk):
                global_sno = p_idx * CHUNK_SIZE + r_i + 1
                row_cells = table.rows[r_i + 1].cells
                row_cells[0].text = str(global_sno)
                row_cells[1].text = st['adm_no']
                row_cells[2].text = st['name']
                row_cells[3].text = st['room_allotted']

                for c_i, cell in enumerate(row_cells):
                    cell.width = col_widths[c_i]
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i in [0, 1, 3] else WD_ALIGN_PARAGRAPH.LEFT
                    if p.runs:
                        p.runs[0].font.name = 'Times New Roman'
                        p.runs[0].font.size = Pt(9)
                        if c_i == 3:
                            p.runs[0].font.bold = True
                    set_cell_border(cell, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                                          bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                                          left={"sz": 2, "val": "single", "color": "CCCCCC"},
                                          right={"sz": 2, "val": "single", "color": "CCCCCC"})

    doc.save(output_path)
    return output_path

# ==============================================================================
# 2. ROOMWISE DISPLAY LIST (ROOMWISE LIST TO DISPLAY PA1 2026-27.docx)
# ==============================================================================
def generate_roomwise_display_docx(output_path):
    data = get_seating_plan_data()
    settings = data['settings']
    rooms_summary = data['rooms_summary']

    exam_title = settings.get('exam_title', 'Periodic Assessment – 2')
    acad_year = settings.get('academic_year', '2026-27')

    doc = docx.Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.4)
        sec.bottom_margin = Inches(0.4)
        sec.left_margin = Inches(0.5)
        sec.right_margin = Inches(0.5)

    CHUNK_SIZE = 26
    is_first_page = True

    for rm in rooms_summary:
        if rm['total_seated'] == 0:
            continue

        all_students = rm.get('name_sorted_students') or rm['all_students']
        chunks = [all_students[i:i + CHUNK_SIZE] for i in range(0, len(all_students), CHUNK_SIZE)] or [[]]

        for p_idx, chunk in enumerate(chunks):
            if not is_first_page:
                doc.add_page_break()
            is_first_page = False

            add_header_banner(doc, banner_type='wide')

            p_t = doc.add_paragraph()
            p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_t.paragraph_format.space_before = Pt(2)
            p_t.paragraph_format.space_after = Pt(1)
            r_t = p_t.add_run(f"{exam_title} ({acad_year})\nRoom wise List")
            r_t.font.name = 'Times New Roman'
            r_t.font.size = Pt(12)
            r_t.font.bold = True

            p_r = doc.add_paragraph()
            p_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_r.paragraph_format.space_before = Pt(1)
            p_r.paragraph_format.space_after = Pt(4)
            page_suffix = f" (Page {p_idx+1})" if len(chunks) > 1 else ""
            r_rn = p_r.add_run(f"ROOM NAME : {rm['name']}{page_suffix} (TOTAL {rm['total_seated']})")
            r_rn.font.name = 'Times New Roman'
            r_rn.font.size = Pt(11)
            r_rn.font.bold = True

            add_horizontal_straight_line(doc)

            # Single full-width table across page: S.No, Admi.No, Name of Candidate, Class & Sec
            table = doc.add_table(rows=len(chunk) + 1, cols=4)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            make_table_header_repeat(table, 1)

            col_w = [Inches(0.6), Inches(1.3), Inches(3.8), Inches(1.5)]

            # Header row
            sub_headers = ['S.No', 'Admi.No', 'Name of Candidate', 'Class & Sec']
            hdr1 = table.rows[0]
            for c_i, sh in enumerate(sub_headers):
                cell = hdr1.cells[c_i]
                cell.width = col_w[c_i]
                cell.text = sh
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if p.runs:
                    p.runs[0].font.name = 'Times New Roman'
                    p.runs[0].font.size = Pt(9)
                    p.runs[0].font.bold = True
                set_cell_background(cell, 'F1F5F9')
                set_cell_border(cell, top={"sz": 4, "val": "single", "color": "000000"},
                                      bottom={"sz": 4, "val": "single", "color": "000000"},
                                      left={"sz": 2, "val": "single", "color": "000000"},
                                      right={"sz": 2, "val": "single", "color": "000000"})

            for r_i, st in enumerate(chunk):
                global_sno = p_idx * CHUNK_SIZE + r_i + 1
                row_cells = table.rows[r_i + 1].cells
                for c_i in range(4):
                    row_cells[c_i].width = col_w[c_i]

                row_cells[0].text = str(global_sno)
                row_cells[1].text = st['adm_no']
                row_cells[2].text = st['name']
                row_cells[3].text = st['seating_group'] or st['class_name']

                for c_i, cell in enumerate(row_cells):
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(1.5)
                    p.paragraph_format.space_after = Pt(1.5)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i in [0, 1, 3] else WD_ALIGN_PARAGRAPH.LEFT
                    if p.runs:
                        p.runs[0].font.name = 'Times New Roman'
                        p.runs[0].font.size = Pt(8.5)
                    set_cell_border(cell, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                                          bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                                          left={"sz": 2, "val": "single", "color": "CCCCCC"},
                                          right={"sz": 2, "val": "single", "color": "CCCCCC"})

    doc.save(output_path)
    return output_path

# ==============================================================================
# 3. ATTENDANCE SHEET DOCX (PA 2 ATTANDENCE SHEET 2026-27.docx)
# ==============================================================================
def generate_attendance_sheet_docx(output_path):
    data = get_seating_plan_data()
    settings = data['settings']
    attendance_dates = data['attendance_dates']
    rooms_summary = data['rooms_summary']

    exam_title = settings.get('exam_title', 'Periodic Assessment – 2')
    acad_year = settings.get('academic_year', '2026-27')

    doc = docx.Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.4)
        sec.bottom_margin = Inches(0.4)
        sec.left_margin = Inches(0.4)
        sec.right_margin = Inches(0.4)

    for idx, rm in enumerate(rooms_summary):
        if rm['total_seated'] == 0:
            continue
        if idx > 0:
            doc.add_page_break()

        add_header_banner(doc, banner_type='wide')

        p_t = doc.add_paragraph()
        p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_t.paragraph_format.space_before = Pt(2)
        p_t.paragraph_format.space_after = Pt(1)
        r_t = p_t.add_run(f"{exam_title} ({acad_year})\nAttendance sheet")
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(12)
        r_t.font.bold = True

        p_r = doc.add_paragraph()
        p_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_r.paragraph_format.space_before = Pt(1)
        p_r.paragraph_format.space_after = Pt(4)
        r_rn = p_r.add_run(f"ROOM NAME : {rm['name']}")
        r_rn.font.name = 'Times New Roman'
        r_rn.font.size = Pt(11)
        r_rn.font.bold = True

        add_horizontal_straight_line(doc)

        students = rm['all_students']
        num_date_cols = len(attendance_dates) or 8
        total_cols = 4 + num_date_cols

        table = doc.add_table(rows=len(students) + 6, cols=total_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        make_table_header_repeat(table, 2)

        # Row 0: Dates
        hdr0 = table.rows[0]
        hdr0.cells[0].text = 'S.No'
        hdr0.cells[1].text = 'Admi.No'
        hdr0.cells[2].text = 'Name of the Students'
        hdr0.cells[3].text = 'Class & Sec'

        # Row 1: Days
        hdr1 = table.rows[1]
        hdr1.cells[0].text = 'S.No'
        hdr1.cells[1].text = 'Admi.No'
        hdr1.cells[2].text = 'Name of the Students'
        hdr1.cells[3].text = 'Class & Sec'

        for d_idx, dt in enumerate(attendance_dates):
            c_pos = 4 + d_idx
            raw_d = dt.get('date', '')
            if '-' in raw_d and len(raw_d) == 10:
                parts = raw_d.split('-')
                disp_d = f"{parts[2]}/{parts[1]}"
            else:
                disp_d = raw_d
            hdr0.cells[c_pos].text = disp_d
            hdr1.cells[c_pos].text = dt.get('day', '')

        # Merge headers vertically for first 4 columns
        for c_i in range(4):
            hdr0.cells[c_i].merge(hdr1.cells[c_i])

        for r_hdr in [hdr0, hdr1]:
            for c_i in range(total_cols):
                cell = r_hdr.cells[c_i]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if p.runs:
                    p.runs[0].font.name = 'Times New Roman'
                    p.runs[0].font.size = Pt(8.5)
                    p.runs[0].font.bold = True
                set_cell_background(cell, 'F1F5F9')
                set_cell_border(cell, top={"sz": 4, "val": "single", "color": "000000"},
                                      bottom={"sz": 4, "val": "single", "color": "000000"},
                                      left={"sz": 2, "val": "single", "color": "000000"},
                                      right={"sz": 2, "val": "single", "color": "000000"})

        for r_i, st in enumerate(students):
            row_cells = table.rows[r_i + 2].cells
            row_cells[0].text = str(r_i + 1)
            row_cells[1].text = st['adm_no']
            row_cells[2].text = st['name']
            row_cells[3].text = st['seating_group'] or st['class_name']

            for c_i in range(total_cols):
                cell = row_cells[c_i]
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i in [0, 1, 3] else (WD_ALIGN_PARAGRAPH.LEFT if c_i == 2 else WD_ALIGN_PARAGRAPH.CENTER)
                if p.runs:
                    p.runs[0].font.name = 'Times New Roman'
                    p.runs[0].font.size = Pt(8)
                set_cell_border(cell, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                                      bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                                      left={"sz": 2, "val": "single", "color": "CCCCCC"},
                                      right={"sz": 2, "val": "single", "color": "CCCCCC"})

        # 4 Daily summary rows inside table (TOTAL, NO. OF PRESENT, NO. OF ABSENT, SIGN. OF THE INVIGILATOR)
        summary_rows_def = [
            ('TOTAL', str(len(students)), True),
            ('NO. OF PRESENT', '', False),
            ('NO . OF ABSENT', '', False),
            ('SIGN. OF THE INVIGILATOR', '', False)
        ]

        base_r = len(students) + 2
        for s_idx, (label, val, is_total) in enumerate(summary_rows_def):
            s_row = table.rows[base_r + s_idx]
            s_row.cells[2].text = label
            p = s_row.cells[2].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if is_total else WD_ALIGN_PARAGRAPH.LEFT
            if p.runs:
                p.runs[0].font.name = 'Times New Roman'
                p.runs[0].font.size = Pt(8)
                p.runs[0].font.bold = True

            if is_total:
                s_row.cells[3].text = val
                p3 = s_row.cells[3].paragraphs[0]
                p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if p3.runs:
                    p3.runs[0].font.name = 'Times New Roman'
                    p3.runs[0].font.size = Pt(8)
                    p3.runs[0].font.bold = True

            for c_i in range(total_cols):
                cell = s_row.cells[c_i]
                if is_total:
                    set_cell_background(cell, 'F1F5F9')
                set_cell_border(cell, top={"sz": 2, "val": "single", "color": "000000"},
                                      bottom={"sz": 2, "val": "single", "color": "000000"},
                                      left={"sz": 2, "val": "single", "color": "000000"},
                                      right={"sz": 2, "val": "single", "color": "000000"})

    doc.save(output_path)
    return output_path

# ==============================================================================
# 4. MASTER SEATING SUMMARY DOCX (SEATING ARRANGEMENTS PA-2 2026.docx)
# ==============================================================================
def generate_master_summary_docx(output_path):
    data = get_seating_plan_data()
    settings = data['settings']
    rooms_summary = data['rooms_summary']
    all_students = data['all_students']

    exam_title = settings.get('exam_title', 'Periodic Assessment – 2')
    acad_year = settings.get('academic_year', '2026-27')

    doc = docx.Document()
    for sec in doc.sections:
        sec.top_margin = Inches(0.4)
        sec.bottom_margin = Inches(0.4)
        sec.left_margin = Inches(0.5)
        sec.right_margin = Inches(0.5)

    add_header_banner(doc, banner_type='wide')

    p_t = doc.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t.paragraph_format.space_before = Pt(4)
    p_t.paragraph_format.space_after = Pt(6)
    r_t = p_t.add_run(f"{exam_title} Seating Arrangements {acad_year}")
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(13)
    r_t.font.bold = True

    add_horizontal_straight_line(doc)

    # Girls Block Table
    p_gb = doc.add_paragraph()
    p_gb.paragraph_format.space_before = Pt(4)
    p_gb.paragraph_format.space_after = Pt(2)
    r_gb = p_gb.add_run("GIRLS BLOCK SEATING ARRANGEMENTS")
    r_gb.font.name = 'Times New Roman'
    r_gb.font.size = Pt(11)
    r_gb.font.bold = True

    girls_rooms = [rm for rm in rooms_summary if rm['block'] == 'Girls Block']
    t_gb = doc.add_table(rows=len(girls_rooms) + 1, cols=5)
    t_gb.alignment = WD_TABLE_ALIGNMENT.CENTER
    make_table_header_repeat(t_gb, 1)

    headers_m = ['Room Name', 'Left Row (L)', 'Right Row (R)', 'Total Seated', 'Capacity']
    for c_i, h in enumerate(headers_m):
        cell = t_gb.rows[0].cells[c_i]
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(9.5)
        p.runs[0].font.bold = True
        set_cell_background(cell, 'F1F5F9')
        set_cell_border(cell, top={"sz": 4, "val": "single", "color": "000000"},
                              bottom={"sz": 4, "val": "single", "color": "000000"},
                              left={"sz": 2, "val": "single", "color": "000000"},
                              right={"sz": 2, "val": "single", "color": "000000"})

    for r_i, rm in enumerate(girls_rooms):
        row_cells = t_gb.rows[r_i + 1].cells
        row_cells[0].text = rm['name']
        
        # Summarize left classes
        left_summary = defaultdict(list)
        for st in rm['left_students']:
            left_summary[st['seating_group'] or st['class_name']].append(st['roll_in_group'])
        left_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in left_summary.items()])
        row_cells[1].text = left_txt

        # Summarize right classes
        right_summary = defaultdict(list)
        for st in rm['right_students']:
            right_summary[st['seating_group'] or st['class_name']].append(st['roll_in_group'])
        right_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in right_summary.items()])
        row_cells[2].text = right_txt

        row_cells[3].text = str(rm['total_seated'])
        row_cells[4].text = f"{rm['capacity']} ({rm['benches']} benches)"

        for c_i, cell in enumerate(row_cells):
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i in [0, 3, 4] else WD_ALIGN_PARAGRAPH.LEFT
            if p.runs:
                p.runs[0].font.name = 'Times New Roman'
                p.runs[0].font.size = Pt(8.5)
            set_cell_border(cell, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                                  bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                                  left={"sz": 2, "val": "single", "color": "CCCCCC"},
                                  right={"sz": 2, "val": "single", "color": "CCCCCC"})

    # Boys Block Table
    p_bb = doc.add_paragraph()
    p_bb.paragraph_format.space_before = Pt(8)
    p_bb.paragraph_format.space_after = Pt(2)
    r_bb = p_bb.add_run("BOYS BLOCK SEATING ARRANGEMENTS")
    r_bb.font.name = 'Times New Roman'
    r_bb.font.size = Pt(11)
    r_bb.font.bold = True

    boys_rooms = [rm for rm in rooms_summary if rm['block'] == 'Boys Block']
    t_bb = doc.add_table(rows=len(boys_rooms) + 1, cols=5)
    t_bb.alignment = WD_TABLE_ALIGNMENT.CENTER
    make_table_header_repeat(t_bb, 1)

    for c_i, h in enumerate(headers_m):
        cell = t_bb.rows[0].cells[c_i]
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.name = 'Times New Roman'
        p.runs[0].font.size = Pt(9.5)
        p.runs[0].font.bold = True
        set_cell_background(cell, 'F1F5F9')
        set_cell_border(cell, top={"sz": 4, "val": "single", "color": "000000"},
                              bottom={"sz": 4, "val": "single", "color": "000000"},
                              left={"sz": 2, "val": "single", "color": "000000"},
                              right={"sz": 2, "val": "single", "color": "000000"})

    for r_i, rm in enumerate(boys_rooms):
        row_cells = t_bb.rows[r_i + 1].cells
        row_cells[0].text = rm['name']
        
        left_summary = defaultdict(list)
        for st in rm['left_students']:
            left_summary[st['seating_group'] or st['class_name']].append(st['roll_in_group'])
        left_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in left_summary.items()])
        row_cells[1].text = left_txt

        right_summary = defaultdict(list)
        for st in rm['right_students']:
            right_summary[st['seating_group'] or st['class_name']].append(st['roll_in_group'])
        right_txt = " // ".join([f"{c}: {min(rolls)}-{max(rolls)} ({len(rolls)})" for c, rolls in right_summary.items()])
        row_cells[2].text = right_txt

        row_cells[3].text = str(rm['total_seated'])
        row_cells[4].text = f"{rm['capacity']} ({rm['benches']} benches)"

        for c_i, cell in enumerate(row_cells):
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i in [0, 3, 4] else WD_ALIGN_PARAGRAPH.LEFT
            if p.runs:
                p.runs[0].font.name = 'Times New Roman'
                p.runs[0].font.size = Pt(8.5)
            set_cell_border(cell, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                                  bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                                  left={"sz": 2, "val": "single", "color": "CCCCCC"},
                                  right={"sz": 2, "val": "single", "color": "CCCCCC"})

    # Subject Exemptions Tables
    hifz_students = [s for s in all_students if s['is_hifz']]
    hindi_students = [s for s in all_students if s['is_hindi']]

    p_ex = doc.add_paragraph()
    p_ex.paragraph_format.space_before = Pt(8)
    p_ex.paragraph_format.space_after = Pt(2)
    r_ex = p_ex.add_run(f"SUBJECT EXEMPTIONS (Hifz: {len(hifz_students)}, Hindi: {len(hindi_students)})")
    r_ex.font.name = 'Times New Roman'
    r_ex.font.size = Pt(11)
    r_ex.font.bold = True

    t_ex = doc.add_table(rows=3, cols=3)
    t_ex.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_ex.rows[0].cells[0].text = "Category"
    t_ex.rows[0].cells[1].text = "Count"
    t_ex.rows[0].cells[2].text = "Student Names"
    set_cell_background(t_ex.rows[0].cells[0], 'F1F5F9')
    set_cell_background(t_ex.rows[0].cells[1], 'F1F5F9')
    set_cell_background(t_ex.rows[0].cells[2], 'F1F5F9')

    t_ex.rows[1].cells[0].text = "HIFZ STUDENTS"
    t_ex.rows[1].cells[1].text = str(len(hifz_students))
    t_ex.rows[1].cells[2].text = ", ".join([s['name'] for s in hifz_students[:25]]) + ("..." if len(hifz_students) > 25 else "")

    t_ex.rows[2].cells[0].text = "HINDI STUDENTS"
    t_ex.rows[2].cells[1].text = str(len(hindi_students))
    t_ex.rows[2].cells[2].text = ", ".join([s['name'] for s in hindi_students[:25]]) + ("..." if len(hindi_students) > 25 else "")

    for r in t_ex.rows:
        for c in r.cells:
            set_cell_border(c, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                               bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                               left={"sz": 2, "val": "single", "color": "CCCCCC"},
                               right={"sz": 2, "val": "single", "color": "CCCCCC"})

    doc.save(output_path)
    return output_path
