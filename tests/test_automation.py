"""
End-to-end integration tests using Playwright against the local dummy page.
"""
from pathlib import Path
import pytest
import socket
import threading
import http.server
import socketserver
from playwright.sync_api import sync_playwright

from src.excel_reader import load_and_validate_workbook
from src.automation import MaterialLineAutomation
from src.models import MaterialLineRecord

SAMPLE_EXCEL_PATH = Path(__file__).parent.parent / "data" / "sample_material_lines.xlsx"
WEB_DIR = Path(__file__).parent.parent / "web"

PORTAL_MOCK = """<!doctype html><html><body>
<input name="wspf_10_mll_udfchar03">
<input name="wspf_10_mll_udfnum01">
<input name="wspf_10_mll_udfchar05">
<input name="wspf_10_mll_udfchar09">
<input name="wspf_10_mll_udfchar16">
<script>
document.querySelector('[name="wspf_10_mll_udfchar16"]').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    setTimeout(() => document.querySelectorAll('input').forEach(el => el.value = ''), 20);
  }
});
</script></body></html>"""

def make_portal_mock(tmp_path, reset=True):
    html = PORTAL_MOCK if reset else PORTAL_MOCK.replace(
        "setTimeout(() => document.querySelectorAll('input').forEach(el => el.value = ''), 20);",
        "/* deliberately leave the form populated */",
    )
    path = tmp_path / "portal_mock.html"
    path.write_text(html, encoding="utf-8")
    return path.as_uri()

@pytest.fixture(scope="session")
def local_server_url():
    """Starts a local HTTP server on a free port for the test session."""
    # Find free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(WEB_DIR), **kwargs)
        def log_message(self, format, *args):
            pass

    server = socketserver.TCPServer(("127.0.0.1", port), QuietHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    yield f"http://127.0.0.1:{port}/index.html"
    server.shutdown()

def test_full_sample_run_saves_and_verifies_all_7_rows(local_server_url):
    """
    Run the automation against the local dummy page using the exact seven sample rows.
    Verify:
    1. Exactly seven lines are saved in the table.
    2. Lines are saved in the same order as the workbook.
    3. Every saved Part, Qty, Site, Cost Code, and WBS matches the Excel row.
    4. '2026_2.2.1.' specifically retains its final period.
    """
    records = load_and_validate_workbook(SAMPLE_EXCEL_PATH, expected_row_count=7)

    automation = MaterialLineAutomation(
        target_url=local_server_url,
        headless=True,
        slow_mo=0
    )

    report = automation.run(records, is_dry_run=False, workbook_path=str(SAMPLE_EXCEL_PATH))

    assert report.total_rows == 7
    assert report.successful_rows == 7
    assert report.failed_rows == 0
    assert report.skipped_rows == 0
    assert report.stop_reason is None

    # Verify that each row passed verification and matches exact expected values
    for idx, (res, expected) in enumerate(zip(report.row_results, records)):
        assert res.status == "SUCCESS"
        assert res.verification_passed is True
        assert res.item_code == expected.item_code
        assert res.quantity == expected.quantity
        assert res.site_id == expected.site_id
        assert res.cost_code == expected.cost_code
        assert res.cost_code == "2026_2.2.1."  # Trailing period verified
        assert res.wbs == expected.wbs

        # Check DOM verified values captured
        assert res.verified_values is not None
        assert res.verified_values["part"] == expected.item_code
        assert res.verified_values["qty"] == expected.quantity
        assert res.verified_values["site"] == expected.site_id
        assert res.verified_values["cost_code"] == expected.cost_code
        assert res.verified_values["wbs"] == expected.wbs
        assert res.verified_values["cost_code"].endswith(".")

def test_missing_required_value_rejected_without_silent_save(local_server_url):
    """
    Test that a record missing a required field (e.g. empty Part or empty WBS)
    is rejected with a visible error and does not silently save an incomplete line.
    """
    # Create invalid record with missing Part
    invalid_record = MaterialLineRecord(
        row_index=10,
        item_code="",  # Empty part
        quantity=5,
        site_id="TZKA8027",
        cost_code="2026_2.2.1.",
        wbs="TZKA8027-1795051262"
    )

    automation = MaterialLineAutomation(
        target_url=local_server_url,
        headless=True,
        slow_mo=0
    )

    report = automation.run([invalid_record], is_dry_run=False)

    assert report.total_rows == 1
    assert report.successful_rows == 0
    assert report.failed_rows == 1
    assert report.row_results[0].status == "FAILED"
    assert "Missing required field" in (report.row_results[0].error_message or "")
    assert report.stop_reason is not None

def test_failed_save_stops_batch_without_duplicate_retries(local_server_url):
    """
    Test that when an invalid record is encountered in a batch, the automation
    halts immediately, marking subsequent rows as SKIPPED, avoiding duplicate saves.
    """
    batch = [
        # Valid row 1
        MaterialLineRecord(
            row_index=2,
            item_code="CABL00058",
            quantity=1,
            site_id="TZKA8027",
            cost_code="2026_2.2.1.",
            wbs="TZKA8027-1795051262"
        ),
        # Invalid row 2 (zero quantity)
        MaterialLineRecord(
            row_index=3,
            item_code="CABL00059",
            quantity=0,  # Invalid
            site_id="TZKA8027",
            cost_code="2026_2.2.1.",
            wbs="TZKA8027-1795051262"
        ),
        # Row 3 (should be skipped)
        MaterialLineRecord(
            row_index=4,
            item_code="DBDS00031",
            quantity=1,
            site_id="TZKA8027",
            cost_code="2026_2.2.1.",
            wbs="TZKA8027-1795051262"
        ),
    ]

    automation = MaterialLineAutomation(
        target_url=local_server_url,
        headless=True,
        slow_mo=0
    )

    report = automation.run(batch, is_dry_run=False)

    assert report.total_rows == 3
    assert report.successful_rows == 1
    assert report.failed_rows == 1
    assert report.skipped_rows == 1

    assert report.row_results[0].status == "SUCCESS"
    assert report.row_results[1].status == "FAILED"
    assert report.row_results[2].status == "SKIPPED"
    assert "Quantity must be a valid positive number" in (report.row_results[1].error_message or "")

def test_dry_run_mode_does_not_save_rows(local_server_url):
    """
    Test that dry-run mode validates page controls and rows without adding rows to the table.
    """
    records = load_and_validate_workbook(SAMPLE_EXCEL_PATH, expected_row_count=7)

    automation = MaterialLineAutomation(
        target_url=local_server_url,
        headless=True,
        slow_mo=0
    )

    report = automation.run(records, is_dry_run=True, workbook_path=str(SAMPLE_EXCEL_PATH))

    assert report.is_dry_run is True
    assert report.total_rows == 7
    assert len(report.row_results) == 7
    for res in report.row_results:
        assert res.status == "DRY_RUN"
        assert res.verification_passed is True

    # Double-check that table in page has 0 rows
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(local_server_url)
        assert page.locator('[data-testid="material-line-row"]').count() == 0
        browser.close()

def test_portal_mode_enters_rows_and_does_not_claim_save_verification(tmp_path):
    records = load_and_validate_workbook(SAMPLE_EXCEL_PATH, expected_row_count=7)
    automation = MaterialLineAutomation(
        target_url=make_portal_mock(tmp_path),
        headless=True,
        slow_mo=0,
        portal_mode=True,
        transition_timeout_ms=1000,
    )

    report = automation.run(records, workbook_path=str(SAMPLE_EXCEL_PATH))

    assert report.entered_rows == 7
    assert report.successful_rows == 0
    assert report.failed_rows == 0
    assert report.uncertain_rows == 0
    assert all(result.status == "ENTER_SENT" for result in report.row_results)
    assert all(result.verification_passed is False for result in report.row_results)

def test_portal_mode_stops_after_enter_if_form_does_not_reset(tmp_path):
    records = load_and_validate_workbook(SAMPLE_EXCEL_PATH, expected_row_count=7)
    automation = MaterialLineAutomation(
        target_url=make_portal_mock(tmp_path, reset=False),
        headless=True,
        slow_mo=0,
        portal_mode=True,
        transition_timeout_ms=200,
    )

    report = automation.run(records, workbook_path=str(SAMPLE_EXCEL_PATH))

    assert report.entered_rows == 0
    assert report.uncertain_rows == 1
    assert report.row_results[0].status == "UNCERTAIN"
    assert all(result.status == "SKIPPED" for result in report.row_results[1:])
    assert report.stop_reason
