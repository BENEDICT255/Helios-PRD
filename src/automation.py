"""Excel-driven material-line entry for the local demo and Helios PRD."""

from typing import List, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
    sync_playwright,
)

from src.models import MaterialLineRecord, RowResult, RunReport


class MaterialLineAutomation:
    # Names copied from the user's actual PRD form input elements.
    PORTAL_FIELDS = {
        "part": "wspf_10_mll_udfchar03",
        "quantity": "wspf_10_mll_udfnum01",
        "site": "wspf_10_mll_udfchar05",
        "cost_code": "wspf_10_mll_udfchar09",
        "wbs": "wspf_10_mll_udfchar16",
    }

    def __init__(
        self,
        target_url: str,
        headless: bool = False,
        slow_mo: int = 150,
        timeout_ms: int = 10000,
        cdp_url: Optional[str] = None,
        portal_mode: bool = False,
        transition_timeout_ms: int = 8000,
    ):
        self.target_url = target_url
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout_ms = timeout_ms
        self.cdp_url = cdp_url
        self.portal_mode = portal_mode
        self.transition_timeout_ms = transition_timeout_ms

    def run(
        self,
        records: List[MaterialLineRecord],
        is_dry_run: bool = False,
        workbook_path: str = "",
    ) -> RunReport:
        report = RunReport(
            workbook_path=workbook_path,
            target_url=self.target_url,
            is_dry_run=is_dry_run,
            portal_mode=self.portal_mode,
            total_rows=len(records),
        )

        browser: Optional[Browser] = None
        is_cdp = bool(self.cdp_url)

        try:
            with sync_playwright() as playwright:
                try:
                    if is_cdp:
                        browser = playwright.chromium.connect_over_cdp(
                            self.cdp_url
                        )
                        context, page = self._get_cdp_page(browser)
                    else:
                        browser = playwright.chromium.launch(
                            headless=self.headless,
                            slow_mo=self.slow_mo,
                        )
                        context = browser.new_context(
                            viewport={"width": 1400, "height": 900}
                        )
                        page = context.new_page()

                    page.set_default_timeout(self.timeout_ms)

                    if not is_cdp:
                        page.goto(
                            self.target_url,
                            wait_until="domcontentloaded",
                        )

                    if self.portal_mode:
                        portal_frame = self._verify_portal_controls(page)
                        if is_dry_run:
                            self._record_portal_dry_run_results(records, report)
                        else:
                            self._execute_portal_entry(
                                portal_frame, records, report
                            )
                    else:
                        self._verify_page_controls(page)
                        if is_dry_run:
                            self._record_dry_run_results(records, report)
                        else:
                            self._execute_live_entry(page, records, report)

                except Exception as exc:
                    if not report.stop_reason:
                        report.stop_reason = (
                            f"Automation stopped safely: {type(exc).__name__}: "
                            f"{exc}"
                        )

                finally:
                    # Do not close the user's Chrome session when attached over CDP.
                    if browser is not None and not is_cdp:
                        browser.close()

        except Exception as exc:
            if not report.stop_reason:
                report.stop_reason = (
                    f"Could not start browser automation: "
                    f"{type(exc).__name__}: {exc}"
                )

        report.finalize()
        return report

    def _get_cdp_page(self, browser: Browser):
        """Attach only to the already-open tab matching the supplied ticket URL."""
        contexts = browser.contexts
        if not contexts:
            raise RuntimeError(
                "The attached Chrome session has no browser context."
            )

        context: BrowserContext = contexts[0]
        pages = context.pages

        target = self.target_url.strip().rstrip("/")
        matching_page = next(
            (
                candidate
                for candidate in pages
                if candidate.url.strip().rstrip("/") == target
            ),
            None,
        )
        if matching_page is None:
            raise RuntimeError(
                "No open Chrome tab exactly matches the Portal URL. Open the "
                "intended Site Material Request on its Lines tab, copy that "
                "tab's URL into the launcher, and try again. No lines were entered."
            )
        return context, matching_page

    def _verify_portal_controls(self, page: Page):
        """Find exactly one visible, editable set of the five known PRD fields."""
        matching_frames = []
        for frame in page.frames:
            locators = {
                field: frame.locator(f'input[name="{name}"]')
                for field, name in self.PORTAL_FIELDS.items()
            }
            try:
                if all(locator.count() == 1 for locator in locators.values()):
                    if all(
                        locator.is_visible() and locator.is_enabled()
                        for locator in locators.values()
                    ):
                        matching_frames.append((frame, locators))
            except Exception:
                continue

        if len(matching_frames) != 1:
            raise RuntimeError(
                "Could not identify one unambiguous visible set of all five "
                "PRD fields. Confirm the request is open on the Lines tab and "
                "the five required inputs are visible. No lines were entered."
            )

        frame, locators = matching_frames[0]
        for field, locator in locators.items():
            if locator.get_attribute("aria-readonly") == "true":
                raise RuntimeError(
                    f"The PRD {field} field is read-only. No lines were entered."
                )
        return frame

    def _record_portal_dry_run_results(
        self, records: List[MaterialLineRecord], report: RunReport
    ) -> None:
        """Record workbook readiness; this does not submit or verify any row."""
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
                    verification_passed=False,
                )
            )

    def _execute_portal_entry(
        self, frame, records: List[MaterialLineRecord], report: RunReport
    ) -> None:
        """Fill five PRD fields, press Enter once, then wait for form reset.

        A reset is only used to pace the next row. The tool does not inspect the
        grid and does not claim that the server saved the line; the user reviews
        the Lines grid after the batch.
        """
        selectors = {
            field: frame.locator(f'input[name="{name}"]')
            for field, name in self.PORTAL_FIELDS.items()
        }
        values_for = lambda record: {
            "part": str(record.item_code),
            "quantity": str(record.quantity),
            "site": str(record.site_id),
            "cost_code": str(record.cost_code),
            "wbs": str(record.wbs),
        }

        # Never overwrite values the user already placed in the form.
        if any(locator.input_value().strip() for locator in selectors.values()):
            raise RuntimeError(
                "At least one PRD field already contains a value. Clear or "
                "review the form manually before starting. No lines were entered."
            )

        for index, record in enumerate(records):
            enter_sent = False
            try:
                expected = values_for(record)
                for field in self.PORTAL_FIELDS:
                    selectors[field].fill(expected[field])

                actual = {
                    field: locator.input_value()
                    for field, locator in selectors.items()
                }
                if actual != expected:
                    raise RuntimeError(
                        "The entered field values did not exactly match the "
                        "Excel row; Enter was not pressed."
                    )

                # User-confirmed workflow: Enter on the WBS field submits one line.
                selectors["wbs"].press("Enter")
                enter_sent = True

                # Wait for the input form to reset before sending another row.
                # This is a pacing/safety signal, not confirmation of server save.
                frame.wait_for_function(
                    "names => names.every(name => { const el = "
                    "document.querySelector(`input[name=\"${name}\"]`); "
                    "return el && el.value === ''; })",
                    arg=list(self.PORTAL_FIELDS.values()),
                    timeout=self.transition_timeout_ms,
                )

                report.row_results.append(
                    self._portal_row_result(record, "ENTER_SENT")
                )

            except Exception as exc:
                if enter_sent:
                    message = (
                        "Enter was sent, but the form did not return to a "
                        "blank state. This row's save is uncertain. Review it "
                        "in PRD before rerunning anything."
                    )
                    report.row_results.append(
                        self._portal_row_result(record, "UNCERTAIN", message)
                    )
                else:
                    message = f"Row was not submitted: {type(exc).__name__}: {exc}"
                    report.row_results.append(
                        self._portal_row_result(record, "FAILED", message)
                    )

                report.stop_reason = (
                    f"Stopped at Excel row {record.row_index}; remaining rows "
                    "were not entered. Review the PRD page before any retry."
                )
                for remaining in records[index + 1 :]:
                    report.row_results.append(
                        self._portal_row_result(
                            remaining,
                            "SKIPPED",
                            "Skipped because the previous row needs review.",
                        )
                    )
                break

    @staticmethod
    def _portal_row_result(record, status: str, message: Optional[str] = None):
        return RowResult(
            row_index=record.row_index,
            item_code=record.item_code,
            quantity=record.quantity,
            site_id=record.site_id,
            cost_code=record.cost_code,
            wbs=record.wbs,
            status=status,
            verification_passed=False,
            error_message=message,
        )

    def _verify_page_controls(self, page: Page) -> None:
        """Check that the local demo page has exactly one of each required control."""
        required_test_ids = [
            "input-part",
            "input-qty",
            "input-site",
            "input-cost-code",
            "input-wbs",
            "status-message",
            "material-line-row",
        ]

        for test_id in required_test_ids:
            locator = page.locator(f'[data-testid="{test_id}"]')
            expect(locator).to_have_count(
                1 if test_id != "material-line-row" else locator.count(),
                timeout=self.timeout_ms,
            )

        for test_id in [
            "input-part",
            "input-qty",
            "input-site",
            "input-cost-code",
            "input-wbs",
        ]:
            expect(
                page.locator(f'[data-testid="{test_id}"]')
            ).to_be_visible()

    def _record_dry_run_results(
        self,
        records: List[MaterialLineRecord],
        report: RunReport,
    ) -> None:
        """Report workbook rows as checked without saving any page entries."""
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
                    error_message=None,
                )
            )

    def _execute_live_entry(
        self,
        page: Page,
        records: List[MaterialLineRecord],
        report: RunReport,
    ) -> None:
        """
        Enter rows one at a time on the page.

        Despite the method's existing name, this implementation is for the
        local demo only because it uses demo-only data-testid selectors.
        """
        part_input = page.locator('[data-testid="input-part"]')
        qty_input = page.locator('[data-testid="input-qty"]')
        site_input = page.locator('[data-testid="input-site"]')
        cost_code_input = page.locator('[data-testid="input-cost-code"]')
        wbs_input = page.locator('[data-testid="input-wbs"]')
        status_banner = page.locator('[data-testid="status-message"]')
        rows_locator = page.locator(
            '[data-testid="material-line-row"]'
        )

        saved_count = 0
        baseline_rows = rows_locator.count()

        for index, record in enumerate(records):
            try:
                # Fill the five required fields from this Excel record.
                part_input.fill(str(record.item_code))
                qty_input.fill(str(record.quantity))
                site_input.fill(str(record.site_id))
                cost_code_input.fill(str(record.cost_code))
                wbs_input.fill(str(record.wbs))

                # Save once. Never retry an uncertain submission.
                wbs_input.press("Enter")

                expected_rows = baseline_rows + saved_count + 1

                # Wait until the row appears or the page reports a validation error.
                page.wait_for_function(
                    """
                    (args) => {
                        const rows = document.querySelectorAll(
                            args.rowSelector
                        ).length;
                        const banner = document.querySelector(
                            args.statusSelector
                        );

                        const className = banner
                            ? String(banner.className || "")
                            : "";
                        const text = banner
                            ? String(banner.innerText || "").trim()
                            : "";

                        return (
                            rows >= args.expectedRows ||
                            className.includes("status-error") ||
                            text.startsWith("Validation Error")
                        );
                    }
                    """,
                    arg={
                        "rowSelector": (
                            '[data-testid="material-line-row"]'
                        ),
                        "statusSelector": (
                            '[data-testid="status-message"]'
                        ),
                        "expectedRows": expected_rows,
                    },
                    timeout=self.timeout_ms,
                )

                status_text = status_banner.inner_text().strip()
                status_class = status_banner.get_attribute("class") or ""

                if (
                    "status-error" in status_class
                    or status_text.startswith("Validation Error")
                ):
                    self._append_failed_result(
                        report,
                        record,
                        f"Page rejected the line: {status_text}",
                    )
                    self._stop_and_skip_remaining(
                        records[index + 1 :],
                        report,
                        record.row_index,
                    )
                    break

                current_rows = rows_locator.count()
                if current_rows != expected_rows:
                    self._append_failed_result(
                        report,
                        record,
                        (
                            "Unexpected row count after save: "
                            f"expected {expected_rows}, found {current_rows}."
                        ),
                    )
                    self._stop_and_skip_remaining(
                        records[index + 1 :],
                        report,
                        record.row_index,
                    )
                    break

                latest_row = rows_locator.nth(current_rows - 1)

                saved_part = self._cell_text(latest_row, "part")
                saved_qty_text = self._cell_text(latest_row, "qty")
                saved_site = self._cell_text(latest_row, "site")
                saved_cost_code = self._cell_text(
                    latest_row,
                    "cost-code",
                )
                saved_wbs = self._cell_text(latest_row, "wbs")
                saved_line_text = self._cell_text(latest_row, "line")

                saved_qty = self._parse_integer(saved_qty_text)
                saved_line_no = self._parse_integer(saved_line_text)

                verified_values = {
                    "part": saved_part,
                    "qty": saved_qty,
                    "site": saved_site,
                    "cost_code": saved_cost_code,
                    "wbs": saved_wbs,
                    "line": saved_line_no,
                }

                mismatches = []

                if saved_part != str(record.item_code):
                    mismatches.append(
                        f"Part expected {record.item_code!r}, "
                        f"got {saved_part!r}"
                    )

                if saved_qty != int(record.quantity):
                    mismatches.append(
                        f"Qty expected {record.quantity!r}, "
                        f"got {saved_qty_text!r}"
                    )

                if saved_site != str(record.site_id):
                    mismatches.append(
                        f"Site expected {record.site_id!r}, "
                        f"got {saved_site!r}"
                    )

                if saved_cost_code != str(record.cost_code):
                    mismatches.append(
                        f"Cost Code expected {record.cost_code!r}, "
                        f"got {saved_cost_code!r}"
                    )

                if saved_wbs != str(record.wbs):
                    mismatches.append(
                        f"WBS expected {record.wbs!r}, "
                        f"got {saved_wbs!r}"
                    )

                if mismatches:
                    self._append_failed_result(
                        report,
                        record,
                        "Saved row verification failed: "
                        + "; ".join(mismatches),
                        saved_line_no=saved_line_no,
                        verified_values=verified_values,
                    )
                    self._stop_and_skip_remaining(
                        records[index + 1 :],
                        report,
                        record.row_index,
                    )
                    break

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
                        verified_values=verified_values,
                    )
                )

            except PlaywrightTimeoutError as exc:
                self._append_failed_result(
                    report,
                    record,
                    (
                        "Timed out waiting for a clear save result. "
                        "The row was not retried to avoid a duplicate. "
                        f"Details: {exc}"
                    ),
                )
                self._stop_and_skip_remaining(
                    records[index + 1 :],
                    report,
                    record.row_index,
                )
                break

            except Exception as exc:
                self._append_failed_result(
                    report,
                    record,
                    (
                        "Unexpected error while entering or verifying the row. "
                        "The row was not retried. "
                        f"{type(exc).__name__}: {exc}"
                    ),
                )
                self._stop_and_skip_remaining(
                    records[index + 1 :],
                    report,
                    record.row_index,
                )
                break

    @staticmethod
    def _cell_text(row, field_name: str) -> str:
        return row.locator(
            f'[data-field="{field_name}"]'
        ).inner_text().strip()

    @staticmethod
    def _parse_integer(value: str) -> Optional[int]:
        value = value.strip()
        if value.isdigit():
            return int(value)
        return None

    @staticmethod
    def _append_failed_result(
        report: RunReport,
        record: MaterialLineRecord,
        error_message: str,
        saved_line_no: Optional[int] = None,
        verified_values: Optional[dict] = None,
    ) -> None:
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
                error_message=error_message,
                verified_values=verified_values,
            )
        )

    @staticmethod
    def _stop_and_skip_remaining(
        remaining: List[MaterialLineRecord],
        report: RunReport,
        failed_row_index: int,
    ) -> None:
        if not report.stop_reason:
            report.stop_reason = (
                f"Execution stopped at row {failed_row_index}. "
                "Remaining rows were skipped."
            )

        for record in remaining:
            report.row_results.append(
                RowResult(
                    row_index=record.row_index,
                    item_code=record.item_code,
                    quantity=record.quantity,
                    site_id=record.site_id,
                    cost_code=record.cost_code,
                    wbs=record.wbs,
                    status="SKIPPED",
                    verification_passed=False,
                    error_message="Skipped because an earlier row failed.",
                )
            )
