"""
Excel template generator for Helios PRD Material Lines.
Produces a clean, user-ready template with the 5 required columns and sample guide.
"""
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

TEMPLATE_HEADERS = [
    ("Item Code", 18, "Part code in catalog (e.g. CABL00058)"),
    ("Quantity Req Per Site", 24, "Positive number (e.g. 1)"),
    ("Site ID", 18, "Site identifier (e.g. TZKA8027)"),
    ("Line", 20, "Cost Code - SAP Budget Line (e.g. 2026_2.2.1.)"),
    ("WBS", 26, "WBS and Project Code (e.g. TZKA8027-1795051262)")
]

def generate_excel_template(target_path: Path) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Material Lines Entry"

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
    hint_font = Font(name="Segoe UI", size=9, italic=True, color="64748B")
    border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

    # Row 1: Headers
    for col_idx, (header_name, col_width, hint) in enumerate(TEMPLATE_HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = cell_border
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = col_width

    # Row 2: Helpful column hints
    for col_idx, (_, _, hint) in enumerate(TEMPLATE_HEADERS, start=1):
        cell = ws.cell(row=2, column=col_idx, value=f"Format: {hint}")
        cell.font = hint_font
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = cell_border

    # Format data rows 3-100 as text / number format
    for row in range(3, 50):
        for col_idx in range(1, 6):
            cell = ws.cell(row=row, column=col_idx)
            cell.border = cell_border
            if col_idx == 2:
                cell.number_format = "0"
            else:
                cell.number_format = "@"

    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(target_path)
    return target_path

if __name__ == "__main__":
    out = Path("data/Helios_Material_Lines_Template.xlsx")
    generate_excel_template(out)
    print(f"Template created at: {out.resolve()}")
