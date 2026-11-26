import os
import json
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from database import get_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(BASE_DIR, 'consolidated_subject_mapping.json')
BANNER_WIDE_PATH = os.path.join(BASE_DIR, 'static', 'images', 'school_banner_wide.png')

# Default class sheet mappings if json is absent
CLASS_SHEET_MAP = {
    '6 A': 'GR 6A',
    '6 B': 'GR 6B',
    '6 C': 'GR 6C',
    '6 HIFZ': 'GR 6 HIFZ',
    '7 A': 'GR 7 A',
    '7 B': 'GR 7 B',
    '7 HIFZ2': 'GR 7 HIFZ (2)',
    '8 A': 'GR 8 A',
    '8 B': 'GR 8 B',
    '9 A': 'GR 9 A',
    '9 B': 'GR 9 B)',
    '9 C': 'GR 9 C',
    '10 A': 'GR 10  A ',
    '10 B': 'GR 10 B',
    '10 C': 'GR 10 C',
    '10 D': 'GR 10 D',
    '11': 'GR 11',
    '12': 'gr 12'
}

def load_subject_mapping():
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_consolidated_sheet_data():
    conn = get_db()
    cursor = conn.cursor()

    # Settings
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    exam_title = settings.get('exam_title', 'Periodic Assessment – 2')
    academic_year = settings.get('academic_year', '2026-27')

    # Students grouped by class
    cursor.execute("SELECT * FROM students WHERE active = 1 ORDER BY class_name ASC, roll_in_class ASC, adm_no ASC")
    student_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    students_by_class = defaultdict(list)
    for s in student_rows:
        students_by_class[s['class_name']].append(s)

    mapping = load_subject_mapping()

    # Define standard class order
    order_keys = [
        '6 A', '6 B', '6 C', '6 HIFZ',
        '7 A', '7 B', '7 HIFZ2',
        '8 A', '8 B',
        '9 A', '9 B', '9 C',
        '10 A', '10 B', '10 C', '10 D',
        '11', '12'
    ]

    all_db_classes = list(students_by_class.keys())
    ordered_classes = [c for c in order_keys if c in all_db_classes]
    for c in all_db_classes:
        if c not in ordered_classes:
            ordered_classes.append(c)

    classes_data = []
    for cls in ordered_classes:
        st_list = students_by_class.get(cls, [])
        sheet_key = CLASS_SHEET_MAP.get(cls, cls)
        sheet_info = mapping.get(sheet_key, {})
        
        subjects = sheet_info.get('subjects', [])
        # If subjects is empty (fallback default)
        if not subjects:
            subjects = [
                {'name': 'ENGLISH', 'marks': '( 80 M )', 'category': ''},
                {'name': 'URDU / HINDI', 'marks': '( 80 M )', 'category': ''},
                {'name': 'TELUGU', 'marks': '( 80 M )', 'category': ''},
                {'name': 'MATHS', 'marks': '( 80 M )', 'category': ''},
                {'name': 'SCIENCE', 'marks': '( 80 M )', 'category': ''},
                {'name': 'SOCIAL', 'marks': '( 80 M )', 'category': ''},
                {'name': 'A I', 'marks': '( 40 M )', 'category': 'Skill Subject'},
                {'name': 'Quran', 'marks': '( 50 M )', 'category': 'Add.Sub'},
                {'name': 'Height', 'marks': '', 'category': ''},
                {'name': 'Weight', 'marks': '', 'category': ''},
                {'name': 'ATTENDANCE', 'marks': '(   )', 'category': ''}
            ]

        classes_data.append({
            'class_name': cls,
            'display_name': f"Class {cls}",
            'sheet_name': sheet_key,
            'subjects': subjects,
            'students': st_list,
            'total_students': len(st_list)
        })

    return {
        'settings': settings,
        'exam_title': exam_title,
        'academic_year': academic_year,
        'classes': classes_data
    }

def set_docx_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_docx_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn(f'w:{key}'), str(val))

# ==============================================================================
# 1. EXCEL EXPORTER (.xlsx) - Exact Multi-Sheet Replica for Marks Entry
# ==============================================================================
def generate_consolidated_excel(output_path):
    data = get_consolidated_sheet_data()
    classes = data['classes']
    exam_title = data['exam_title']
    acad_year = data['academic_year']

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    header_font_title = Font(name='Calibri', size=13, bold=True, color='000000')
    header_font_cols = Font(name='Calibri', size=10, bold=True, color='000000')
    marks_font = Font(name='Calibri', size=9, bold=True, color='1E3A8A')
    data_font = Font(name='Calibri', size=10, bold=False, color='000000')
    data_font_bold = Font(name='Calibri', size=10, bold=True, color='000000')

    title_fill = PatternFill(start_color='E2E8F0', end_color='E2E8F0', fill_type='solid')
    header_fill = PatternFill(start_color='F1F5F9', end_color='F1F5F9', fill_type='solid')
    marks_fill = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')

    thin_border_side = Side(style='thin', color='000000')
    thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    light_border_side = Side(style='thin', color='CBD5E1')
    light_border = Border(left=light_border_side, right=light_border_side, top=light_border_side, bottom=light_border_side)

    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='center')

    for c_info in classes:
        sheet_title = c_info['sheet_name'][:31]
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True

        subjects = c_info['subjects']
        total_cols = 3 + len(subjects)

        # Row 1: Class Name & Assessment Title
        ws.cell(1, 1, value=c_info['display_name'])
        ws.cell(1, 1).font = header_font_title
        ws.cell(1, 1).alignment = align_left

        title_text = f"{exam_title} ({acad_year}) CONSOLIDATED SHEET"
        ws.cell(1, 3, value=title_text)
        ws.cell(1, 3).font = header_font_title
        ws.cell(1, 3).alignment = align_center

        # Row 2: Headers (S.No, Adm.No, Student Name, Subjects...)
        ws.cell(2, 1, value='S.No')
        ws.cell(2, 2, value='Adm.No')
        ws.cell(2, 3, value='Student Name')

        for i, subj in enumerate(subjects):
            col_idx = 4 + i
            ws.cell(2, col_idx, value=subj['name'])
            ws.cell(3, col_idx, value=subj['marks'])

        # Format header rows 2 and 3
        for c in range(1, total_cols + 1):
            cell2 = ws.cell(2, c)
            cell2.font = header_font_cols
            cell2.fill = header_fill
            cell2.border = thin_border
            cell2.alignment = align_center if c != 3 else align_left

            cell3 = ws.cell(3, c)
            cell3.font = marks_font
            cell3.fill = marks_fill
            cell3.border = thin_border
            cell3.alignment = align_center

        # Student data rows
        students = c_info['students']
        for r_i, st in enumerate(students):
            row_idx = 4 + r_i
            s_sno = ws.cell(row_idx, 1, value=r_i + 1)
            s_adm = ws.cell(row_idx, 2, value=st['adm_no'])
            s_name = ws.cell(row_idx, 3, value=st['name'])

            s_sno.font = data_font
            s_sno.alignment = align_center
            s_sno.border = light_border

            s_adm.font = data_font_bold
            s_adm.alignment = align_center
            s_adm.border = light_border

            s_name.font = data_font_bold
            s_name.alignment = align_left
            s_name.border = light_border

            # Blank cells for marks entry with clean grid border
            for c in range(4, total_cols + 1):
                mark_cell = ws.cell(row_idx, c, value='')
                mark_cell.font = data_font
                mark_cell.alignment = align_center
                mark_cell.border = light_border

        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 7
        ws.column_dimensions['B'].width = 14
        ws.column_dimensions['C'].width = 30
        for c in range(4, total_cols + 1):
            col_letter = get_column_letter(c)
            ws.column_dimensions[col_letter].width = 12

    wb.save(output_path)
    return output_path

# ==============================================================================
# 2. WORD EXPORTER (.docx) - A4 Landscape Document for Direct Printing & Marks
# ==============================================================================
def generate_consolidated_docx(output_path):
    data = get_consolidated_sheet_data()
    classes = data['classes']
    exam_title = data['exam_title']
    acad_year = data['academic_year']

    doc = docx.Document()
    
    # Configure A4 Landscape
    for sec in doc.sections:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width = Inches(11.69)
        sec.page_height = Inches(8.27)
        sec.top_margin = Inches(0.4)
        sec.bottom_margin = Inches(0.4)
        sec.left_margin = Inches(0.4)
        sec.right_margin = Inches(0.4)

    for idx, c_info in enumerate(classes):
        if idx > 0:
            doc.add_page_break()

        # Banner image
        if os.path.exists(BANNER_WIDE_PATH):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run()
            run.add_picture(BANNER_WIDE_PATH, width=Inches(10.89))

        # Title
        p_t = doc.add_paragraph()
        p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_t.paragraph_format.space_before = Pt(2)
        p_t.paragraph_format.space_after = Pt(1)
        r_t = p_t.add_run(f"{exam_title} ({acad_year})\nCONSOLIDATED MARKS SHEET")
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(12)
        r_t.font.bold = True

        # Class line
        p_c = doc.add_paragraph()
        p_c.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_c.paragraph_format.space_before = Pt(1)
        p_c.paragraph_format.space_after = Pt(4)
        r_c = p_c.add_run(f"CLASS: {c_info['display_name']}\t\tTOTAL STUDENTS: {c_info['total_students']}\t\tClass Tr. Signature: ______________")
        r_c.font.name = 'Times New Roman'
        r_c.font.size = Pt(10)
        r_c.font.bold = True

        # Divider line
        p_line = doc.add_paragraph()
        p_line.paragraph_format.space_before = Pt(1)
        p_line.paragraph_format.space_after = Pt(4)
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '12')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), '000000')
        pBdr.append(bottom)
        p_line._p.get_or_add_pPr().append(pBdr)

        # Table
        students = c_info['students']
        subjects = c_info['subjects']
        total_cols = 3 + len(subjects)

        table = doc.add_table(rows=len(students) + 2, cols=total_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Set repeat header rows
        for r_i in range(2):
            trPr = table.rows[r_i]._tr.get_or_add_trPr()
            trPr.append(OxmlElement('w:tblHeader'))

        # Row 0: Subjects
        hdr0 = table.rows[0]
        hdr0.cells[0].text = 'S.No'
        hdr0.cells[1].text = 'Adm.No'
        hdr0.cells[2].text = 'Student Name'

        # Row 1: Marks
        hdr1 = table.rows[1]
        hdr1.cells[0].text = 'S.No'
        hdr1.cells[1].text = 'Adm.No'
        hdr1.cells[2].text = 'Student Name'

        for s_idx, subj in enumerate(subjects):
            c_pos = 3 + s_idx
            hdr0.cells[c_pos].text = subj['name']
            hdr1.cells[c_pos].text = subj['marks']

        # Merge first 3 columns vertically
        for c_i in range(3):
            hdr0.cells[c_i].merge(hdr1.cells[c_i])

        for r_hdr in [hdr0, hdr1]:
            for c_i in range(total_cols):
                cell = r_hdr.cells[c_i]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if p.runs:
                    p.runs[0].font.name = 'Times New Roman'
                    p.runs[0].font.size = Pt(7.5)
                    p.runs[0].font.bold = True
                set_docx_cell_background(cell, 'F1F5F9')
                set_docx_cell_border(cell, top={"sz": 4, "val": "single", "color": "000000"},
                                           bottom={"sz": 4, "val": "single", "color": "000000"},
                                           left={"sz": 2, "val": "single", "color": "000000"},
                                           right={"sz": 2, "val": "single", "color": "000000"})

        # Student rows
        for r_i, st in enumerate(students):
            row_cells = table.rows[r_i + 2].cells
            row_cells[0].text = str(r_i + 1)
            row_cells[1].text = st['adm_no']
            row_cells[2].text = st['name']

            for c_i in range(total_cols):
                cell = row_cells[c_i]
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_i in [0, 1] else (WD_ALIGN_PARAGRAPH.LEFT if c_i == 2 else WD_ALIGN_PARAGRAPH.CENTER)
                if p.runs:
                    p.runs[0].font.name = 'Times New Roman'
                    p.runs[0].font.size = Pt(7.5)
                set_docx_cell_border(cell, top={"sz": 2, "val": "single", "color": "CCCCCC"},
                                           bottom={"sz": 2, "val": "single", "color": "CCCCCC"},
                                           left={"sz": 2, "val": "single", "color": "CCCCCC"},
                                           right={"sz": 2, "val": "single", "color": "CCCCCC"})

    doc.save(output_path)
    return output_path
