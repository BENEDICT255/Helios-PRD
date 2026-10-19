"""
Playwright-based automation engine for Material Line entry.
Features:
- Label/test-id based selectors (no coordinates or image recognition).
- Row-by-row entry and immediate 5-field table verification.
- Stop on first failure or ambiguous save (no duplicate retries).
- Dry-run mode support.
- Configurable headless/visible browser execution.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

from src.models import MaterialLineRecord, RowResult, RunReport

class MaterialLineAutomation:
    def __init__(
        self,
        target_url: str,
        headless: bool = False,
        slow_mo: int = 150,  # Milliseconds delay between actions for visibility
        timeout_ms: int = 10000,
        cdp_url: Optional[str] = None
    ):
        self.target_url = target_url
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout_ms = timeout_ms
        self.cdp_url = cdp_url

    def run(
        self,
        records: List[MaterialLineRecord],
        is_dry_run: bool = False,
        workbook_path: str = ""
    ) -> RunReport:
        report = RunReport(
            workbook_path=workbook_path,
            target_url=self.target_url,
            is_dry_run=is_dry_run,
            total_rows=len(records)
        )

        with sync_playwright() as p:
            is_cdp = bool(self.cdp_url)
            if is_cdp:
                browser = p.chromium.connect_over_cdp(self.cdp_url)
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(self.timeout_ms)
                if self.target_url and self.target_url not in page.url:
                    page.goto(self.target_url, wait_until="domcontentloaded")
            else:
                browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
                context = browser.new_context(viewport={"width": 1400, "height": 900})
                page = context.new_page()
                page.set_default_timeout(self.timeout_ms)
                page.goto(self.target_url, wait_until="domcontentloaded")

                # Verify page loaded and controls are available
                self._verify_page_controls(page)

                if is_dry_run:
                    # In dry-run mode, validate controls exist without saving lines
                    for record in records:
                        report.row_results.append(
                            RowResult(
                                row_index=record.row_index,
                                item_code=record.item_code,
                                quantity=record.quantity,
                                site_id=record.site_id,
                                cost_code=record.cost_code,
                                wbs=record.wbs,
                                status="DRY_RUN",
                                verification_passed=True,
                                error_message=None
                            )
                        )
                else:
                    self._execute_live_entry(page, records, report)

            except Exception as exc:
                if not report.stop_reason:
                    report.stop_reason = f"Fatal automation error: {str(exc)}"
            finally:
                report.finalize()
                if not is_cdp:
                    browser.close()

        return report

    def _verify_page_controls(self, page: Page):
        """Verifies that the required inputs and actions exist on the target page."""
        expect(page.locator('[data-testid="input-part"]')).to_be_visible()
        expect(page.locator('[data-testid="input-qty"]')).to_be_visible()
        expect(page.locator('[data-testid="input-site"]')).to_be_visible()
        expect(page.locator('[data-testid="input-cost-code"]')).to_be_visible()
        expect(page.locator('[data-testid="input-wbs"]')).to_be_visible()
        expect(page.locator('[data-testid="status-message"]')).to_be_visible()

    def _execute_live_entry(
        self,
        page: Page,
        records: List[MaterialLineRecord],
        report: RunReport
    ):
        part_input = page.locator('[data-testid="input-part"]')
        qty_input = page.locator('[data-testid="input-qty"]')
        site_input = page.locator('[data-testid="input-site"]')
        cost_code_input = page.locator('[data-testid="input-cost-code"]')
        wbs_input = page.locator('[data-testid="input-wbs"]')
        status_banner = page.locator('[data-testid="status-message"]')
        rows_locator = page.locator('[data-testid="material-line-row"]')

        saved_count = 0

        for idx, record in enumerate(records):
            # 1. Fill input fields
            part_input.fill(record.item_code)
            qty_input.fill(str(record.quantity))
            site_input.fill(record.site_id)
            cost_code_input.fill(record.cost_code)
            wbs_input.fill(record.wbs)

            # 2. Submit by pressing Enter (matches Helios PRD behavior)
            wbs_input.press("Enter")

            # 3. Check status banner response
            status_text = status_banner.inner_text().strip()
            status_class = status_banner.get_attribute("class") or ""

            if "status-error" in status_class or status_text.startswith("Validation Error"):
                err_msg = f"Save rejected by page: {status_text}"
                report.row_results.append(
                    RowResult(
                        row_index=record.row_index,
                        item_code=record.item_code,
                        quantity=record.quantity,
                        site_id=record.site_id,
                        cost_code=record.cost_code,
                        wbs=record.wbs,
                        status="FAILED",
                        verification_passed=False,
                        error_message=err_msg
                    )
                )
                report.stop_reason = f"Execution halted at row {record.row_index}: {err_msg}"
                self._mark_remaining_as_skipped(records[idx + 1:], report)
                break

            if "status-success" not in status_class and "saved successfully" not in status_text:
                err_msg = f"Ambiguous save state: status is '{status_text}'"
                report.row_results.append(
                    RowResult(
                        row_index=record.row_index,
                        item_code=record.item_code,
                        quantity=record.quantity,
                        site_id=record.site_id,
                        cost_code=record.cost_code,
                        wbs=record.wbs,
                        status="FAILED",
                        verification_passed=False,
                        error_message=err_msg
                    )
                )
                report.stop_reason = f"Execution halted at row {record.row_index}: {err_msg}"
                self._mark_remaining_as_skipped(records[idx + 1:], report)
                break

            # 4. Immediate Table Verification
            current_table_rows = rows_locator.count()
            expected_table_rows = saved_count + 1

            if current_table_rows != expected_table_rows:
                err_msg = (
                    f"Row count mismatch after save: expected {expected_table_rows} rows in table, "
                    f"found {current_table_rows}"
                )
                report.row_results.append(
                    RowResult(
                        row_index=record.row_index,
                        item_code=record.item_code,
                        quantity=record.quantity,
                        site_id=record.site_id,
                        cost_code=record.cost_code,
                        wbs=record.wbs,
                        status="FAILED",
                        verification_passed=False,
                        error_message=err_msg
                    )
                )
                report.stop_reason = f"Execution halted at row {record.row_index}: {err_msg}"
                self._mark_remaining_as_skipped(records[idx + 1:], report)
                break

            # Inspect latest row
            latest_row = rows_locator.nth(current_table_rows - 1)
            saved_part = latest_row.locator('[data-field="part"]').inner_text().strip()
            saved_qty_str = latest_row.locator('[data-field="qty"]').inner_text().strip()
            saved_site = latest_row.locator('[data-field="site"]').inner_text().strip()
            saved_cost_code = latest_row.locator('[data-field="cost-code"]').inner_text().strip()
            saved_wbs = latest_row.locator('[data-field="wbs"]').inner_text().strip()
            saved_line_str = latest_row.locator('[data-field="line"]').inner_text().strip()

            saved_line_no = int(saved_line_str) if saved_line_str.isdigit() else None
            saved_qty = int(saved_qty_str) if saved_qty_str.isdigit() else None

            verified_values = {
                "part": saved_part,
                "qty": saved_qty,
                "site": saved_site,
                "cost_code": saved_cost_code,
                "wbs": saved_wbs,
                "line": saved_line_no,
            }

            mismatches = []
            if saved_part != record.item_code:
                mismatches.append(f"Part mismatch (expected '{record.item_code}', got '{saved_part}')")
            if saved_qty != record.quantity:
                mismatches.append(f"Qty mismatch (expected {record.quantity}, got {saved_qty})")
            if saved_site != record.site_id:
                mismatches.append(f"Site mismatch (expected '{record.site_id}', got '{saved_site}')")
            if saved_cost_code != record.cost_code:
                mismatches.append(f"Cost Code mismatch (expected '{record.cost_code}', got '{saved_cost_code}')")
            if saved_wbs != record.wbs:
                mismatches.append(f"WBS mismatch (expected '{record.wbs}', got '{saved_wbs}')")

            if mismatches:
                err_msg = "Table row verification failed: " + "; ".join(mismatches)
                report.row_results.append(
                    RowResult(
                        row_index=record.row_index,
                        item_code=record.item_code,
                        quantity=record.quantity,
                        site_id=record.site_id,
                        cost_code=record.cost_code,
                        wbs=record.wbs,
                        status="FAILED",
                        saved_line_no=saved_line_no,
                        verification_passed=False,
                        error_message=err_msg,
                        verified_values=verified_values
                    )
                )
                report.stop_reason = f"Execution halted at row {record.row_index}: {err_msg}"
                self._mark_remaining_as_skipped(records[idx + 1:], report)
                break

            # Success
            saved_count += 1
            report.row_results.append(
                RowResult(
                    row_index=record.row_index,
                    item_code=record.item_code,
                    quantity=record.quantity,
                    site_id=record.site_id,
                    cost_code=record.cost_code,
                    wbs=record.wbs,
                    status="SUCCESS",
                    saved_line_no=saved_line_no,
                    verification_passed=True,
                    error_message=None,
                    verified_values=verified_values
                )
            )

    def _mark_remaining_as_skipped(self, remaining: List[MaterialLineRecord], report: RunReport):
        for rec in remaining:
            report.row_results.append(
                RowResult(
                    row_index=rec.row_index,
                    item_code=rec.item_code,
                    quantity=rec.quantity,
                    site_id=rec.site_id,
                    cost_code=rec.cost_code,
                    wbs=rec.wbs,
                    status="SKIPPED",
                    verification_passed=False,
                    error_message="Skipped due to earlier failure"
                )
            )
