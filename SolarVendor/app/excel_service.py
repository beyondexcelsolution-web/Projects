"""
Excel Export Service using pandas and openpyxl.
Exports comprehensive, clean, professional .xlsx spreadsheets
with formatted headers, auto-adjusted column widths, and currency formatting.
"""

import io
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def format_excel_sheet(ws, title_text="Solar Vendor Export"):
    # Header styling
    header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.row_dimensions[1].height = 28

    # Apply borders and auto-fit column widths
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.font = data_font
            cell.border = thin_border
            if isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

def export_dataframe_to_excel(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]
        format_excel_sheet(ws, sheet_name)
    output.seek(0)
    return output.getvalue()

def export_master_report(tables_dict: dict) -> bytes:
    """
    Exports a multi-sheet master Excel workbook:
    Leads, Projects, Quotations, DISCOM, Invoices, Payments.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, records in tables_dict.items():
            df = pd.DataFrame(records)
            clean_name = sheet_name[:30] # Excel sheet name max 31 chars
            df.to_excel(writer, index=False, sheet_name=clean_name)
            ws = writer.sheets[clean_name]
            format_excel_sheet(ws, clean_name)
    output.seek(0)
    return output.getvalue()
