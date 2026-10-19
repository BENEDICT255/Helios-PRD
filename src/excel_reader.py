"""
Excel workbook reader and strict validator for Material Line entry.
"""
from pathlib import Path
from typing import List, Tuple
import openpyxl

from src.models import MaterialLineRecord

REQUIRED_COLUMNS = [
    "Item Code",
    "Quantity Req Per Site",
    "Site ID",
    "Line",
    "WBS",
]

class WorkbookValidationError(Exception):
    """Raised when the Excel workbook violates schema, data, or integrity constraints."""
    pass

def load_and_validate_workbook(
    file_path: Path,
    expected_row_count: int = None
) -> List[MaterialLineRecord]:
    """
    Reads an Excel file, validates column presence, non-empty cells,
    positive numeric quantities, and text integrity (preserving trailing periods).
    """
    path = Path(file_path)
    if not path.is_file():
        raise WorkbookValidationError(f"Excel file not found at path: {path.resolve()}")

    try:
        # data_only=False to read stored text representations accurately
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:
        raise WorkbookValidationError(f"Failed to open Excel workbook '{path.name}': {exc}") from exc

    sheet = wb.active
    if sheet is None:
        raise WorkbookValidationError(f"Workbook '{path.name}' has no active sheet.")

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        raise WorkbookValidationError(f"Workbook '{path.name}' active sheet is completely empty.")

    header_row = rows[0]
    if not header_row or all(c is None for c in header_row):
        raise WorkbookValidationError(f"Workbook '{path.name}' does not have a valid header row.")

    # Build header map
    normalized_headers = [str(col).strip() if col is not None else "" for col in header_row]
    header_indices = {}
    missing_columns = []

    for required_col in REQUIRED_COLUMNS:
        if required_col in normalized_headers:
            header_indices[required_col] = normalized_headers.index(required_col)
        else:
            missing_columns.append(required_col)

    if missing_columns:
        raise WorkbookValidationError(
            f"Missing required columns in '{path.name}': {', '.join(missing_columns)}. "
            f"Found headers: {normalized_headers}"
        )

    # Process data rows
    data_rows = rows[1:]
    records: List[MaterialLineRecord] = []

    for row_idx, row in enumerate(data_rows, start=2):
        # Skip completely empty trailing rows
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        item_code_val = row[header_indices["Item Code"]]
        qty_val = row[header_indices["Quantity Req Per Site"]]
        site_val = row[header_indices["Site ID"]]
        line_val = row[header_indices["Line"]]
        wbs_val = row[header_indices["WBS"]]

        # Check required fields non-empty
        missing_fields = []
        if item_code_val is None or str(item_code_val).strip() == "":
            missing_fields.append("Item Code")
        if qty_val is None or str(qty_val).strip() == "":
            missing_fields.append("Quantity Req Per Site")
        if site_val is None or str(site_val).strip() == "":
            missing_fields.append("Site ID")
        if line_val is None or str(line_val).strip() == "":
            missing_fields.append("Line")
        if wbs_val is None or str(wbs_val).strip() == "":
            missing_fields.append("WBS")

        if missing_fields:
            raise WorkbookValidationError(
                f"Row {row_idx} is missing required field(s): {', '.join(missing_fields)}"
            )

        # Validate quantity is a valid positive integer/number
        try:
            qty_num = float(qty_val)
            if qty_num <= 0:
                raise ValueError("Quantity must be greater than zero.")
            if qty_num.is_integer():
                qty_int = int(qty_num)
            else:
                qty_int = int(qty_num)  # Or keep as int if whole units
        except (ValueError, TypeError) as err:
            raise WorkbookValidationError(
                f"Row {row_idx} has invalid Quantity '{qty_val}': must be a positive number ({err})"
            )

        # Ensure strings preserve exact characters including trailing dots
        item_code_str = str(item_code_val).strip()
        site_str = str(site_val).strip()
        line_str = str(line_val).strip()
        wbs_str = str(wbs_val).strip()

        records.append(
            MaterialLineRecord(
                row_index=row_idx,
                item_code=item_code_str,
                quantity=qty_int,
                site_id=site_str,
                cost_code=line_str,
                wbs=wbs_str,
            )
        )

    if expected_row_count is not None and len(records) != expected_row_count:
        raise WorkbookValidationError(
            f"Expected exactly {expected_row_count} sample rows, but found {len(records)} valid rows."
        )

    if len(records) == 0:
        raise WorkbookValidationError(f"Workbook '{path.name}' contains no data rows.")

    return records
