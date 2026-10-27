"""
Helios PRD Material Lines Automation - Desktop Launcher GUI
Provides a clean desktop window for downloading templates, selecting workbooks,
choosing target portals, attaching to active SSO sessions, and running automation.
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.excel_reader import load_and_validate_workbook, WorkbookValidationError
from src.template_generator import generate_excel_template
from src.automation import MaterialLineAutomation
from src.reporter import generate_markdown_report, generate_json_report

class HeliosLauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Helios PRD - Material Lines Automation Launcher")
        self.geometry("740x700")
        self.minsize(680, 600)

        # Style configuration
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self._configure_styles()
        self._build_ui()

        # Default paths
        default_excel = PROJECT_ROOT / "data" / "sample_material_lines.xlsx"
        if default_excel.exists():
            self.excel_path_var.set(str(default_excel))
            self._validate_excel_silent(default_excel)

    def _configure_styles(self):
        self.configure(bg="#F1F5F9")
        self.style.configure(".", font=("Segoe UI", 10), background="#F1F5F9")
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#0B5CAB", background="#F1F5F9")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#64748B", background="#F1F5F9")
        self.style.configure("Section.TLabelframe", background="#FFFFFF", padding=12)
        self.style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#1E293B", background="#FFFFFF")
        
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#0B5CAB", foreground="#FFFFFF")
        self.style.map("Primary.TButton", background=[("active", "#08437D")])

        self.style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#E2E8F0", foreground="#1E293B")
        self.style.map("Secondary.TButton", background=[("active", "#CBD5E1")])

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(header_frame, text="Helios PRD Material-Line Entry Automation", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header_frame,
            text="Enter Excel rows into the five required Lines fields; review the result in PRD yourself.",
            style="SubHeader.TLabel"
        ).pack(anchor=tk.W)

        # 2. Excel Template & Workbook Selection Section
        excel_frame = ttk.LabelFrame(main_frame, text="1. Excel workbook", style="Section.TLabelframe")
        excel_frame.pack(fill=tk.X, pady=(0, 10))

        # Template download row
        tpl_row = ttk.Frame(excel_frame, style="White.TFrame")
        tpl_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(tpl_row, text="Need the standard Excel format?", background="#FFFFFF").pack(side=tk.LEFT)
        download_btn = ttk.Button(tpl_row, text="📥 Download Blank Excel Template", style="Secondary.TButton", command=self._download_template)
        download_btn.pack(side=tk.RIGHT)

        # File picker row
        file_row = ttk.Frame(excel_frame)
        file_row.pack(fill=tk.X, pady=(0, 4))
        self.excel_path_var = tk.StringVar()
        entry_file = ttk.Entry(file_row, textvariable=self.excel_path_var, width=54)
        entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        browse_btn = ttk.Button(file_row, text="📁 Browse Excel...", style="Secondary.TButton", command=self._browse_excel)
        browse_btn.pack(side=tk.RIGHT)

        # Validation status badge
        self.validation_status_var = tk.StringVar(value="Waiting for file...")
        self.status_lbl = tk.Label(excel_frame, textvariable=self.validation_status_var, font=("Segoe UI", 9), bg="#FFFFFF", fg="#475569", anchor="w")
        self.status_lbl.pack(fill=tk.X)

        # 3. Target Portal & Connection Mode Section
        target_frame = ttk.LabelFrame(main_frame, text="2. Page URL and mode", style="Section.TLabelframe")
        target_frame.pack(fill=tk.X, pady=(0, 10))

        url_row = ttk.Frame(target_frame)
        url_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(url_row, text="Portal URL:", background="#FFFFFF").pack(side=tk.LEFT, padx=(0, 8))
        self.url_var = tk.StringVar(value="http://127.0.0.1:8000/index.html")
        url_entry = ttk.Entry(url_row, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        # Mode Selection
        mode_row = ttk.Frame(target_frame)
        mode_row.pack(fill=tk.X, pady=(0, 4))
        self.mode_var = tk.StringVar(value="LOCAL")

        rb1 = ttk.Radiobutton(mode_row, text="Local Demo Page", variable=self.mode_var, value="LOCAL", command=self._on_mode_change)
        rb1.pack(side=tk.LEFT, padx=(0, 12))

        rb2 = ttk.Radiobutton(mode_row, text="Attach to Chrome / PRD (Port 9222)", variable=self.mode_var, value="CDP", command=self._on_mode_change)
        rb2.pack(side=tk.LEFT, padx=(0, 12))

        # Advisory hint
        self.mode_hint_var = tk.StringVar(
            value="💡 Local Prototype Mode: Automates against the local dummy Helios PRD page."
        )
        self.mode_hint_lbl = tk.Label(
            target_frame,
            textvariable=self.mode_hint_var,
            font=("Segoe UI", 9, "italic"),
            bg="#FFFFFF",
            fg="#2563EB",
            wraplength=660,
            justify=tk.LEFT,
            anchor="w"
        )
        self.mode_hint_lbl.pack(fill=tk.X, pady=(4, 0))

        # 4. Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.run_btn = ttk.Button(btn_frame, text="▶ Run Automation", style="Primary.TButton", command=self._start_automation)
        self.run_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.dry_btn = ttk.Button(btn_frame, text="🔍 Dry-Run Validation", style="Secondary.TButton", command=self._start_dry_run)
        self.dry_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.open_page_btn = ttk.Button(btn_frame, text="🌐 Open Local Page", style="Secondary.TButton", command=self._open_local_page)
        self.open_page_btn.pack(side=tk.LEFT)

        # 5. Live Console Log
        log_frame = ttk.LabelFrame(main_frame, text="Execution Progress & Log", style="Section.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#1E293B", fg="#F8FAFC", height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self._log("System initialized. Ready for automation.")

    def _log(self, text: str):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "LOCAL":
            self.url_var.set("http://127.0.0.1:8000/index.html")
            self.mode_hint_var.set("💡 Local Prototype Mode: Automates against the local dummy Helios PRD page.")
        elif mode == "CDP":
            self.mode_hint_var.set(
                "PRD mode: use the Chrome window started by start_chrome_sso.bat. Open the test request on Lines, "
                "copy that tab's URL here, and leave all five inputs blank. Enter is sent once per Excel row."
            )
        else:
            self.mode_hint_var.set("🌐 Direct Mode: Playwright will open a new browser window directly to the Portal URL.")

    def _download_template(self):
        target = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="Helios_Material_Lines_Template.xlsx",
            title="Save Blank Material Lines Template"
        )
        if target:
            try:
                generate_excel_template(Path(target))
                messagebox.showinfo("Template Downloaded", f"Excel template saved successfully to:\n{target}")
                self._log(f"[+] Downloaded template to: {target}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save template: {e}")

    def _browse_excel(self):
        filename = filedialog.askopenfilename(
            title="Select Filled Excel Workbook",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if filename:
            self.excel_path_var.set(filename)
            self._validate_excel_silent(Path(filename))

    def _validate_excel_silent(self, path: Path):
        try:
            records = load_and_validate_workbook(path)
            self.validation_status_var.set(f"✅ Valid Workbook: {len(records)} records ready. All 5 required columns verified.")
            self.status_lbl.configure(fg="#16A34A")
            self._log(f"[+] Validated workbook '{path.name}': {len(records)} records found.")
            return records
        except WorkbookValidationError as e:
            self.validation_status_var.set(f"❌ Validation Error: {e}")
            self.status_lbl.configure(fg="#DC2626")
            self._log(f"[-] Workbook validation failed: {e}")
            return None

    def _open_local_page(self):
        import webbrowser
        url = self.url_var.get().strip() or "http://127.0.0.1:8000/index.html"
        webbrowser.open(url)
        self._log(f"[*] Opened {url} in browser.")

    def _start_automation(self):
        self._run_process(is_dry_run=False)

    def _start_dry_run(self):
        self._run_process(is_dry_run=True)

    def _run_process(self, is_dry_run: bool):
        excel_str = self.excel_path_var.get().strip()
        if not excel_str or not Path(excel_str).exists():
            messagebox.showerror("Error", "Please select a valid Excel workbook file first.")
            return

        excel_path = Path(excel_str)
        try:
            records = load_and_validate_workbook(excel_path)
        except WorkbookValidationError as e:
            messagebox.showerror("Workbook Error", str(e))
            return

        target_url = self.url_var.get().strip()
        mode = self.mode_var.get()
        if mode == "CDP":
            if not target_url.lower().startswith(("https://", "http://")):
                messagebox.showerror("Page URL required", "Paste the URL of the open test request's Lines tab.")
                return
            confirmed = messagebox.askokcancel(
                "Confirm PRD line entry",
                f"This will enter {len(records)} Excel rows into the open PRD request and press Enter once per row.\n\n"
                "The tool will not verify saved rows. You will review the Lines grid yourself after it finishes.\n\n"
                "Confirm the open tab is the intended test request and all five input fields are blank.",
                icon="warning",
            )
            if not confirmed:
                return
        cdp_url = "http://127.0.0.1:9222" if mode == "CDP" else None

        self.run_btn.configure(state=tk.DISABLED)
        self.dry_btn.configure(state=tk.DISABLED)
        self._log("\n" + "=" * 60)
        self._log(f"[*] Starting {'DRY RUN' if is_dry_run else 'AUTOMATION'}...")
        self._log(f"[*] Target URL: {target_url}")
        self._log(f"[*] Mode: {mode} (CDP: {cdp_url})")
        self._log(f"[*] Processing {len(records)} material lines...")

        def worker():
            try:
                auto = MaterialLineAutomation(
                    target_url=target_url,
                    headless=False,
                    slow_mo=200,
                    cdp_url=cdp_url,
                    portal_mode=(mode == "CDP"),
                )
                report = auto.run(records, is_dry_run=is_dry_run, workbook_path=str(excel_path))

                # Save report
                md_path = PROJECT_ROOT / "reports" / "run_report.md"
                json_path = PROJECT_ROOT / "reports" / "run_report.json"
                generate_markdown_report(report, md_path)
                generate_json_report(report, json_path)

                self.after(0, lambda: self._show_run_result(report, is_dry_run, mode))

            except Exception as ex:
                self.after(0, lambda error=ex: self._show_run_error(error))
            finally:
                self.after(0, self._enable_run_buttons)

        threading.Thread(target=worker, daemon=True).start()

    def _show_run_result(self, report, is_dry_run: bool, mode: str):
        self._log("[+] Run finished.")
        self._log(
            f"    Total: {report.total_rows} | Demo verified: {report.successful_rows} | "
            f"PRD Enter sent: {report.entered_rows} | Uncertain: {report.uncertain_rows} | "
            f"Failed: {report.failed_rows} | Skipped: {report.skipped_rows}"
        )
        if report.stop_reason:
            self._log(f"    Stopped: {report.stop_reason}")

        if is_dry_run:
            messagebox.showinfo(
                "Dry run complete",
                f"Workbook and page fields are ready for {report.total_rows} rows.\n"
                "No values were entered and nothing was submitted.",
            )
        elif mode == "CDP":
            message = (
                f"Enter was sent for {report.entered_rows} rows.\n"
                f"Rows needing review: {report.uncertain_rows}.\n\n"
                "This tool does not confirm that PRD saved them. Review the Lines grid now. "
                "If a row is uncertain, do not rerun it until you have checked the request."
            )
            if report.stop_reason:
                message += f"\n\nStopped: {report.stop_reason}"
                messagebox.showwarning("Stopped — review PRD before retrying", message)
            else:
                messagebox.showinfo("Review PRD", message)
        elif report.failed_rows == 0:
            messagebox.showinfo(
                "Demo complete",
                f"All {report.successful_rows} demo rows were saved and verified on the local dummy page.",
            )
        else:
            messagebox.showwarning("Batch stopped", report.stop_reason or "A row failed.")

    def _show_run_error(self, error):
        self._log(f"[-] Execution error: {error}")
        messagebox.showerror("Automation error", f"Automation encountered an error:\n{error}")

    def _enable_run_buttons(self):
        self.run_btn.configure(state=tk.NORMAL)
        self.dry_btn.configure(state=tk.NORMAL)

def main():
    app = HeliosLauncherApp()
    app.mainloop()

if __name__ == "__main__":
    main()
