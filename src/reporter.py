"""
Run report generator for Material Line Entry Automation.
Produces detailed Markdown and JSON reports.
"""
import json
from pathlib import Path
from src.models import RunReport

def generate_markdown_report(report: RunReport, output_path: Path) -> Path:
    mode_label = (
        "DRY RUN (no page changes)" if report.is_dry_run
        else "PRD ENTER-ONLY (save not verified)" if report.portal_mode
        else "LOCAL DEMO (rows verified on dummy page)"
    )
    lines = [
        "# Helios PRD - Material Lines Entry Automation Report",
        "",
        "## Summary",
        f"- **Timestamp**: `{report.start_time}` to `{report.end_time}`",
        f"- **Target URL**: `{report.target_url}`",
        f"- **Workbook**: `{report.workbook_path}`",
        f"- **Mode**: `{mode_label}`",
        f"- **Total Rows**: `{report.total_rows}`",
        f"- **Demo rows saved and verified**: `{report.successful_rows}`",
        f"- **PRD Enter presses sent (not save-verified)**: `{report.entered_rows}`",
        f"- **PRD rows needing manual review**: `{report.uncertain_rows}`",
        f"- **Failed / Rejected**: `{report.failed_rows}`",
        f"- **Skipped**: `{report.skipped_rows}`",
        "",
    ]

    if report.stop_reason:
        lines.extend([
            f"> [!WARNING]",
            f"> **Execution Halted Early**: {report.stop_reason}",
            "",
        ])

    lines.extend([
        "## Detailed Row-by-Row Execution",
        "",
        "| Excel Row | Part (Item Code) | Qty | Site | Cost Code - SAP Budget Line | WBS and Project Code | Saved Line # | Status | Verification | Error Details |",
        "| :---: | :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |",
    ])

    for res in report.row_results:
        status_badge = (
            "✅ SUCCESS" if res.status == "SUCCESS"
            else "↵ ENTER SENT — REVIEW" if res.status == "ENTER_SENT"
            else "⚠️ UNCERTAIN — REVIEW" if res.status == "UNCERTAIN"
            else "❌ FAILED" if res.status == "FAILED"
            else "🔍 DRY_RUN" if res.status == "DRY_RUN"
            else "⏭️ SKIPPED"
        )
        line_num = str(res.saved_line_no) if res.saved_line_no is not None else "-"
        verif = "✅ Matched All 5" if res.verification_passed else ("❌ Failed" if res.status == "FAILED" else "-")
        err = res.error_message if res.error_message else "-"

        lines.append(
            f"| {res.row_index} | `{res.item_code}` | {res.quantity} | `{res.site_id}` | `{res.cost_code}` | `{res.wbs}` | {line_num} | {status_badge} | {verif} | {err} |"
        )

    lines.extend([
        "",
        "## Notes",
        "- The local demo verifies saved rows. PRD mode does not inspect the Lines grid or verify server saves; it sends Enter once per Excel row and leaves final review to the user.",
        "- PRD mode waits for the five input fields to clear before continuing. If they do not clear, it stops and marks that row uncertain to prevent accidental duplicate entry.",
        "- No row is retried automatically. Review the PRD Lines grid before running again.",
        "- Excel `Line` values are passed through as text, including a trailing period such as `2026_2.2.1.`.",
        "",
    ])

    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path

def generate_json_report(report: RunReport, output_path: Path) -> Path:
    data = {
        "start_time": report.start_time,
        "end_time": report.end_time,
        "workbook_path": report.workbook_path,
        "target_url": report.target_url,
        "is_dry_run": report.is_dry_run,
        "portal_mode": report.portal_mode,
        "total_rows": report.total_rows,
        "successful_rows": report.successful_rows,
        "entered_rows": report.entered_rows,
        "uncertain_rows": report.uncertain_rows,
        "failed_rows": report.failed_rows,
        "skipped_rows": report.skipped_rows,
        "stop_reason": report.stop_reason,
        "row_results": [
            {
                "row_index": r.row_index,
                "item_code": r.item_code,
                "quantity": r.quantity,
                "site_id": r.site_id,
                "cost_code": r.cost_code,
                "wbs": r.wbs,
                "status": r.status,
                "saved_line_no": r.saved_line_no,
                "verification_passed": r.verification_passed,
                "error_message": r.error_message,
                "verified_values": r.verified_values,
            }
            for r in report.row_results
        ]
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_path
