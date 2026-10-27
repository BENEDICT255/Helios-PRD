"""
Automated unit tests for Excel workbook loading, schema validation, and field preservation.
"""
from pathlib import Path
import pytest
import openpyxl

from src.excel_reader import load_and_validate_workbook, WorkbookValidationError, REQUIRED_COLUMNS

SAMPLE_EXCEL_PATH = Path(__file__).parent.parent / "data" / "sample_material_lines.xlsx"

def test_sample_workbook_exists_and_loads():
    """Verify that the official sample Excel file exists, validates, and has exactly 7 records."""
    records = load_and_validate_workbook(SAMPLE_EXCEL_PATH, expected_row_count=7)
    assert len(records) == 7

    # Check first record mapping
    r0 = records[0]
    assert r0.row_index == 2
    assert r0.item_code == "CABL00058"
    assert r0.quantity == 1
    assert r0.site_id == "TZKA8027"
    assert r0.cost_code == "2026_2.2.1."
    assert r0.wbs == "TZKA8027-1795051262"

def test_trailing_dot_preservation_in_all_records():
    """Specifically verify that '2026_2.2.1.' retains its final period across all 7 records."""
    records = load_and_validate_workbook(SAMPLE_EXCEL_PATH)
    for r in records:
        assert r.cost_code.endswith("."), f"Record at row {r.row_index} lost trailing dot: {r.cost_code}"
        assert r.cost_code == "2026_2.2.1."

def test_missing_column_rejection(tmp_path):
    """Test that missing required columns triggers a WorkbookValidationError."""
    test_file = tmp_path / "missing_cols.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    # Omit 'Line'
    ws.append(["Item Code", "Quantity Req Per Site", "Site ID", "WBS"])
    ws.append(["CABL00058", 1, "TZKA8027", "TZKA8027-1795051262"])
    wb.save(test_file)

    with pytest.raises(WorkbookValidationError, match="Missing required columns.*Line"):
        load_and_validate_workbook(test_file)

def test_empty_required_cell_rejection(tmp_path):
    """Test that a blank required cell in a data row is rejected."""
    test_file = tmp_path / "empty_cell.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(REQUIRED_COLUMNS)
    # Empty site
    ws.append(["CABL00058", 1, "", "2026_2.2.1.", "TZKA8027-1795051262"])
    wb.save(test_file)

    with pytest.raises(WorkbookValidationError, match="Row 2 is missing required field.*Site ID"):
        load_and_validate_workbook(test_file)

def test_invalid_negative_or_zero_quantity(tmp_path):
    """Test that quantity <= 0 or non-numeric is rejected."""
    test_file = tmp_path / "invalid_qty.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(REQUIRED_COLUMNS)
    # Zero quantity
    ws.append(["CABL00058", 0, "TZKA8027", "2026_2.2.1.", "TZKA8027-1795051262"])
    wb.save(test_file)

    with pytest.raises(WorkbookValidationError, match="Row 2 has invalid Quantity '0'"):
        load_and_validate_workbook(test_file)

def test_non_numeric_quantity(tmp_path):
    """Test that string/text quantity is rejected if non-numeric."""
    test_file = tmp_path / "non_num_qty.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(REQUIRED_COLUMNS)
    ws.append(["CABL00058", "Two", "TZKA8027", "2026_2.2.1.", "TZKA8027-1795051262"])
    wb.save(test_file)

    with pytest.raises(WorkbookValidationError, match="Row 2 has invalid Quantity 'Two'"):
        load_and_validate_workbook(test_file)

def test_fractional_quantity_rejected(tmp_path):
    test_file = tmp_path / "fractional_qty.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(REQUIRED_COLUMNS)
    ws.append(["CABL00058", 1.5, "TZKA8027", "2026_2.2.1.", "TZKA8027-1795051262"])
    wb.save(test_file)

    with pytest.raises(WorkbookValidationError, match="whole number"):
        load_and_validate_workbook(test_file)

def test_old_template_hint_row_is_ignored(tmp_path):
    test_file = tmp_path / "old_template.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(REQUIRED_COLUMNS)
    ws.append(["Format: Part code", "Format: Positive number", "Format: Site ID", "Format: Budget line", "Format: WBS"])
    ws.append(["CABL00058", 1, "TZKA8027", "2026_2.2.1.", "TZKA8027-1795051262"])
    wb.save(test_file)

    records = load_and_validate_workbook(test_file)
    assert len(records) == 1
    assert records[0].row_index == 3
    assert records[0].item_code == "CABL00058"
