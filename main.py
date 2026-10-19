"""
Main CLI entry point for Excel-Driven Material-Line Entry Automation.
"""
import argparse
import sys
import threading
import socket
from pathlib import Path

from src.excel_reader import load_and_validate_workbook, WorkbookValidationError
from src.automation import MaterialLineAutomation
from src.reporter import generate_markdown_report, generate_json_report

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def start_background_server(port: int = 8000):
    import http.server
    import socketserver
    web_dir = Path(__file__).parent / "web"
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_dir), **kwargs)
        def log_message(self, format, *args):
            pass

    server = socketserver.TCPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def main():
    parser = argparse.ArgumentParser(
        description="Helios PRD - Excel-Driven Material-Line Entry Automation (Local Prototype)"
    )
    parser.add_argument(
        "--excel",
        type=str,
        default="data/sample_material_lines.xlsx",
        help="Path to the Excel workbook (default: data/sample_material_lines.xlsx)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Target page URL (default: http://localhost:8000/index.html)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate workbook and page controls without saving rows",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: visible browser window)",
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=250,
        help="Delay between actions in milliseconds for visual demonstration (default: 250ms)",
    )
    parser.add_argument(
        "--report-md",
        type=str,
        default="reports/run_report.md",
        help="Path to output markdown report (default: reports/run_report.md)",
    )
    parser.add_argument(
        "--report-json",
        type=str,
        default="reports/run_report.json",
        help="Path to output JSON report (default: reports/run_report.json)",
    )

    args = parser.parse_args()

    excel_path = Path(args.excel).resolve()
    print("=" * 70)
    print("  HELIOS PRD - MATERIAL-LINE ENTRY AUTOMATION (LOCAL PROTOTYPE)")
    print("  [DEMO ONLY - NOT CONNECTED TO PRODUCTION]")
    print("=" * 70)
    print(f"[*] Reading and validating workbook: {excel_path}")

    # Step 1: Validate workbook
    try:
        records = load_and_validate_workbook(excel_path)
        print(f"[+] Workbook validation PASSED. {len(records)} records ready for processing:")
        for r in records:
            print(f"    - Row {r.row_index}: Part={r.item_code}, Qty={r.quantity}, Site={r.site_id}, CostCode='{r.cost_code}', WBS={r.wbs}")
    except WorkbookValidationError as err:
        print(f"[-] WORKBOOK VALIDATION ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Determine target URL and start server if needed
    target_url = args.url
    if not target_url:
        port = 8000
        if not is_port_in_use(port):
            print(f"[*] Starting local background HTTP server on port {port}...")
            start_background_server(port)
        target_url = f"http://127.0.0.1:{port}/index.html"

    print(f"[*] Target dummy page URL: {target_url}")
    print(f"[*] Execution mode: {'DRY RUN (Inspect only)' if args.dry_run else 'LIVE AUTOMATION'}")
    print(f"[*] Browser mode: {'Headless' if args.headless else 'Visible window (visible demo)'}")

    # Step 3: Run automation
    automation = MaterialLineAutomation(
        target_url=target_url,
        headless=args.headless,
        slow_mo=args.slow_mo
    )

    report = automation.run(
        records=records,
        is_dry_run=args.dry_run,
        workbook_path=str(excel_path)
    )

    # Step 4: Write reports
    md_out = generate_markdown_report(report, Path(args.report_md))
    json_out = generate_json_report(report, Path(args.report_json))
    print(f"\n[+] Execution finished. Reports saved:")
    print(f"    - Markdown: {md_out.resolve()}")
    print(f"    - JSON:     {json_out.resolve()}")

    # Print summary
    print("\n" + "=" * 70)
    print("  EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total Rows:               {report.total_rows}")
    print(f"Successfully Saved:       {report.successful_rows}")
    print(f"Failed / Rejected:        {report.failed_rows}")
    print(f"Skipped:                  {report.skipped_rows}")
    if report.stop_reason:
        print(f"Halt Reason:              {report.stop_reason}")
    print("=" * 70)

    if report.failed_rows > 0 or (not args.dry_run and report.successful_rows != report.total_rows):
        sys.exit(2)

if __name__ == "__main__":
    main()
