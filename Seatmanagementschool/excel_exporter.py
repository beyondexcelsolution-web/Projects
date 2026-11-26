import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from seating_engine import get_seating_plan_data

def generate_master_excel(output_path):
    data = get_seating_plan_data()
    settings = data['settings']
    attendance_dates = data['attendance_dates']
    rooms_summary = data['rooms_summary']
    classes_plan = data['classes_plan']
    checks = data['system_checks']
    all_students = data['all_students']
    arrangements = data['arrangements']

    wb = openpyxl.Workbook()
    
    # Fonts & Fills
    font_title = Font(name='Calibri', size=14, bold=True, color='1E293B')
    font_hdr = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    font_bold = Font(name='Calibri', size=10, bold=True)
    font_reg = Font(name='Calibri', size=10)
    
    fill_navy = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    fill_blue = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    fill_gray = PatternFill(start_color='F1F5F9', end_color='F1F5F9', fill_type='solid')
    fill_green = PatternFill(start_color='DCFCE7', end_color='DCFCE7', fill_type='solid')
    
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # -------------------------------------------------------------
    # 1. Sheet: Start Here / Summary
    # -------------------------------------------------------------
    ws_sum = wb.active
    ws_sum.title = "Summary & Health"
    ws_sum.views.sheetView[0].showGridLines = True
    
    ws_sum['B2'] = f"{settings.get('school_name', 'Crescent Islamic School')} - Seating Engine"
    ws_sum['B2'].font = font_title
    ws_sum['B3'] = f"Exam: {settings.get('exam_title', 'Periodic Assessment – 2')} ({settings.get('academic_year', '2026-27')})"
    ws_sum['B3'].font = font_bold
    
    ws_sum['B5'] = "System Integrity Check"
    ws_sum['C5'] = "Value"
    ws_sum['D5'] = "Status"
    for col in ['B', 'C', 'D']:
        ws_sum[f'{col}5'].font = font_hdr
        ws_sum[f'{col}5'].fill = fill_navy

    check_items = [
        ("Students loaded", checks['students_loaded'], "OK"),
        ("Classes found", checks['classes_found'], "OK"),
        ("Rooms in use", f"{checks['rooms_in_use']} / {checks['total_rooms']}", "OK"),
        ("Students without a seat", checks['students_unseated'], "OK" if checks['students_unseated'] == 0 else "ACTION REQUIRED"),
        ("Students placed twice", checks['students_placed_twice'], "OK" if checks['students_placed_twice'] == 0 else "DUPLICATE"),
        ("Plan lines that disagree with list", checks['plan_disagreements'], "OK" if checks['plan_disagreements'] == 0 else "MISMATCH"),
        ("Rooms over bench capacity", checks['rooms_over_capacity'], "OK" if checks['rooms_over_capacity'] == 0 else "OVER BENCH LIMIT")
    ]

    for idx, (label, val, st) in enumerate(check_items):
        r = 6 + idx
        ws_sum[f'B{r}'] = label
        ws_sum[f'C{r}'] = str(val)
        ws_sum[f'D{r}'] = st
        ws_sum[f'B{r}'].font = font_reg
        ws_sum[f'C{r}'].font = font_bold
        ws_sum[f'D{r}'].font = font_bold
        ws_sum[f'D{r}'].fill = fill_green if st == "OK" else fill_gray
        for col in ['B', 'C', 'D']:
            ws_sum[f'{col}{r}'].border = border_thin

    ws_sum.column_dimensions['B'].width = 32
    ws_sum.column_dimensions['C'].width = 15
    ws_sum.column_dimensions['D'].width = 18

    # -------------------------------------------------------------
    # 2. Sheet: Arrangement (The Core Block Plan)
    # -------------------------------------------------------------
    ws_arr = wb.create_sheet(title="Arrangement")
    ws_arr.views.sheetView[0].showGridLines = True
    
    headers_arr = ['Line', 'Room', 'Row (L/R)', 'Class or Group', 'From Roll', 'To Roll', 'Students In Plan']
    for c_i, h in enumerate(headers_arr):
        cell = ws_arr.cell(1, c_i + 1, h)
        cell.font = font_hdr
        cell.fill = fill_blue
        cell.alignment = Alignment(horizontal='center')

    for r_i, arr in enumerate(arrangements):
        r = r_i + 2
        cnt = arr['to_roll'] - arr['from_roll'] + 1
        row_vals = [arr['id'], arr['room_name'], arr['row_side'], arr['class_or_group'], arr['from_roll'], arr['to_roll'], cnt]
        for c_i, v in enumerate(row_vals):
            cell = ws_arr.cell(r, c_i + 1, v)
            cell.font = font_reg
            cell.border = border_thin
            cell.alignment = Alignment(horizontal='center' if c_i in [0, 1, 2, 4, 5, 6] else 'left')

    ws_arr.column_dimensions['A'].width = 8
    ws_arr.column_dimensions['B'].width = 14
    ws_arr.column_dimensions['C'].width = 12
    ws_arr.column_dimensions['D'].width = 18
    ws_arr.column_dimensions['E'].width = 12
    ws_arr.column_dimensions['F'].width = 12
    ws_arr.column_dimensions['G'].width = 16

    # -------------------------------------------------------------
    # 3. Sheet: Rooms
    # -------------------------------------------------------------
    ws_rm = wb.create_sheet(title="Rooms")
    ws_rm.views.sheetView[0].showGridLines = True
    
    headers_rm = ['Room Name', 'Block', 'Benches', 'Seats Capacity', 'Left Row Seated', 'Right Row Seated', 'Total Seated', 'Status']
    for c_i, h in enumerate(headers_rm):
        cell = ws_rm.cell(1, c_i + 1, h)
        cell.font = font_hdr
        cell.fill = fill_navy
        cell.alignment = Alignment(horizontal='center')

    for r_i, rm in enumerate(rooms_summary):
        r = r_i + 2
        row_vals = [rm['name'], rm['block'], rm['benches'], rm['capacity'], rm['left_count'], rm['right_count'], rm['total_seated'], rm['status']]
        for c_i, v in enumerate(row_vals):
            cell = ws_rm.cell(r, c_i + 1, v)
            cell.font = font_reg
            cell.border = border_thin
            cell.alignment = Alignment(horizontal='center' if c_i != 0 else 'left')

    ws_rm.column_dimensions['A'].width = 16
    ws_rm.column_dimensions['B'].width = 14
    ws_rm.column_dimensions['C'].width = 12
    ws_rm.column_dimensions['D'].width = 15
    ws_rm.column_dimensions['E'].width = 16
    ws_rm.column_dimensions['F'].width = 16
    ws_rm.column_dimensions['G'].width = 14
    ws_rm.column_dimensions['H'].width = 14

    # -------------------------------------------------------------
    # 4. Sheet: Class Plan (For Class Teachers)
    # -------------------------------------------------------------
    ws_cp = wb.create_sheet(title="Class Plan")
    ws_cp.views.sheetView[0].showGridLines = True
    
    curr_r = 1
    for c_data in classes_plan:
        ws_cp.cell(curr_r, 1, f"{settings.get('exam_title', 'Periodic Assessment – 2')} - {c_data['display_name']} ({c_data['total_students']} Students)").font = font_bold
        curr_r += 1
        headers_cp = ['S.No', 'Admission No', 'Student Name', 'Class Allocated']
        for c_i, h in enumerate(headers_cp):
            cell = ws_cp.cell(curr_r, c_i + 1, h)
            cell.font = font_hdr
            cell.fill = fill_blue
            cell.alignment = Alignment(horizontal='center')
        curr_r += 1
        for idx, st in enumerate(c_data['students']):
            ws_cp.cell(curr_r, 1, idx + 1).alignment = Alignment(horizontal='center')
            ws_cp.cell(curr_r, 2, st['adm_no']).alignment = Alignment(horizontal='center')
            ws_cp.cell(curr_r, 3, st['name']).alignment = Alignment(horizontal='left')
            ws_cp.cell(curr_r, 4, st['room_allotted']).alignment = Alignment(horizontal='center')
            for col_i in range(1, 5):
                ws_cp.cell(curr_r, col_i).border = border_thin
                ws_cp.cell(curr_r, col_i).font = font_reg
            curr_r += 1
        curr_r += 1

    ws_cp.column_dimensions['A'].width = 8
    ws_cp.column_dimensions['B'].width = 16
    ws_cp.column_dimensions['C'].width = 30
    ws_cp.column_dimensions['D'].width = 16

    wb.save(output_path)
    return output_path
