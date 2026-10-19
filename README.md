# Helios PRD - Excel-Driven Material-Line Entry Automation (Local Prototype)

> **DEMO — LOCAL ONLY**: This is a standalone local prototype built to verify the Excel-to-page automation logic. It does not connect to, open, inspect, or submit anything to the production Helios PRD portal. No production URLs, credentials, tokens, or network calls are used.

---

## 1. Overview & Visual Design
This repository provides a local, end-to-end prototype of an Excel-driven material-line entry automation based on the **Site Material Requests → Lines** screen from Helios PRD (IBM Maximo-style interface).

The prototype consists of:
1. **Desktop GUI Launcher** (`launcher.py`, `run_launcher.bat`):
   - A clean pop-up window to download the standard Excel template, browse/upload filled files, paste the ticket URL, and start automation.
   - Supports both Local Prototype mode and attaching to an active, authenticated Chrome SSO session via remote debugging (port 9222).
2. **Local Dummy Page** (`web/index.html`, `web/styles.css`, `web/app.js`):
   - Recreates the lines grid and two-column line-entry form from the visual reference.
   - Saves lines on **Enter** key press matching real Helios PRD behavior (no Add Line button).
   - Pops up an immediate error message dialog if Enter is pressed before filling all 5 required fields.
   - Prominently displays a persistent `DEMO — LOCAL ONLY` warning banner.
   - Enforces strict validation on all 5 required fields before allowing line creation.
3. **Template & Sample Excel Files** (`data/`):
   - `Helios_Material_Lines_Template.xlsx`: Clean blank template with guidance and formatting.
   - `sample_material_lines.xlsx`: Contains the exact 7 records preserving trailing period on `2026_2.2.1.`.
4. **Python Automation Engine** (`src/automation.py`, `src/excel_reader.py`):
   - Built with **Python 3.12** and **Playwright**.
   - Submits lines by typing the 5 fields and pressing **Enter** into the form.
   - Validates the workbook schema, cell non-emptiness, and positive numeric quantities.
   - Uses stable, label-based and `data-testid` selectors.
   - Performs row-by-row submission with immediate 5-field table verification.
   - Implements a fail-fast halt policy: stops immediately on the first failed or ambiguous save to prevent duplicate records.
   - Supports attaching to existing browser sessions via Chrome DevTools Protocol (CDP).
5. **Test Suite & Reports** (`tests/`, `reports/`):
   - 10 automated tests covering unit validation, trailing dot retention, negative cases, batch halting, and end-to-end browser entry.

---

## 2. Field Mapping Specification

| Excel Column Name | Dummy Page Field Label | Page Control Selector (`data-testid`) | Data Constraint / Verification Rule |
| :--- | :--- | :--- | :--- |
| **Item Code** | **Part** | `input-part` | Required string (e.g. `CABL00058`) |
| **Quantity Req Per Site** | **Qty** | `input-qty` | Required positive number (> 0) |
| **Site ID** | **Site** | `input-site` | Required string (e.g. `TZKA8027`) |
| **Line** | **Cost Code - SAP Budget Line** | `input-cost-code` | Required text; **must preserve trailing dot** (e.g. `2026_2.2.1.`) |
| **WBS** | **WBS and Project Code** | `input-wbs` | Required string (e.g. `TZKA8027-1795051262`) |

---

## 3. Official Sample Data (7 Records)

The workbook `data/sample_material_lines.xlsx` contains exactly these records:

| Item Code | Quantity Req Per Site | Site ID | Line | WBS |
| :--- | :---: | :--- | :--- | :--- |
| `CABL00058` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |
| `CABL00059` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |
| `DBDS00031` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |
| `DBDS00030` | 2 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |
| `DBDS00029` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |
| `DBDS00028` | 2 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |
| `FOKT00004` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` |

---

## 4. Project Structure

```
Material PRD/
├── data/
│   └── sample_material_lines.xlsx   # Source of truth 7-record Excel file
├── web/
│   ├── index.html                   # Maximo-style dummy page with DEMO banner
│   ├── styles.css                   # Enterprise stylesheet matching screenshot
│   └── app.js                       # Client-side validation, rendering, and state
├── src/
│   ├── __init__.py
│   ├── models.py                    # Data classes for records and run reports
│   ├── excel_reader.py              # Strict workbook schema and data validator
│   ├── automation.py                # Playwright automation engine with fail-fast logic
│   └── reporter.py                  # Markdown and JSON report generator
├── tests/
│   ├── test_workbook_validator.py   # Unit tests for schema and trailing dot preservation
│   └── test_automation.py          # Integration tests against local page
├── reports/
│   ├── run_report.md                # Generated execution report
│   ├── run_report.json              # Structured execution report
│   └── screenshots/
│       ├── dummy_page_empty.png     # Screenshot of empty dummy page
│       └── dummy_page_populated.png # Screenshot with all 7 lines saved
├── scripts/
│   └── create_sample_excel.py       # Script that creates sample_material_lines.xlsx
├── main.py                          # CLI runner for the automation
├── serve.py                         # Standalone HTTP server for the dummy page
├── pytest.ini                       # Test runner configuration
└── README.md                        # Documentation and verification guide
```

---

## 5. Setup and Execution Instructions

### Prerequisites
- Python 3.10+ (Python 3.12 used in development)
- Playwright and openpyxl

### Environment Activation
To use the virtual environment created in this project:
```powershell
# In PowerShell:
.\.venv\Scripts\activate
```

If setting up fresh in another environment:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install playwright openpyxl pytest
playwright install chromium
```

### Running the Live Automation Demo
Run the CLI automation tool:
```powershell
# Runs visibly in Chromium with a 250ms visual stepping delay:
python main.py

# Or in headless mode:
python main.py --headless

# Or in dry-run mode (validates workbook and controls without saving):
python main.py --dry-run
```

Options:
- `--excel <path>`: Specify a custom workbook path (defaults to `data/sample_material_lines.xlsx`).
- `--url <url>`: Target URL (defaults to auto-starting background server on `http://127.0.0.1:8000/index.html`).
- `--headless`: Run browser without GUI.
- `--slow-mo <ms>`: Set action delay in milliseconds (default: 250ms).
- `--report-md <path>`: Markdown report output location.
- `--report-json <path>`: JSON report output location.

### Running the Automated Test Suite
Run pytest to verify all 10 unit and integration tests:
```powershell
pytest -v
```

---

## 6. Automated Test Results

All 10 automated test cases passed cleanly:

```
tests/test_automation.py::test_full_sample_run_saves_and_verifies_all_7_rows PASSED     [10%]
tests/test_automation.py::test_missing_required_value_rejected_without_silent_save PASSED [20%]
tests/test_automation.py::test_failed_save_stops_batch_without_duplicate_retries PASSED  [30%]
tests/test_automation.py::test_dry_run_mode_does_not_save_rows PASSED                     [40%]
tests/test_workbook_validator.py::test_sample_workbook_exists_and_loads PASSED          [50%]
tests/test_workbook_validator.py::test_trailing_dot_preservation_in_all_records PASSED  [60%]
tests/test_workbook_validator.py::test_missing_column_rejection PASSED                    [70%]
tests/test_workbook_validator.py::test_empty_required_cell_rejection PASSED             [80%]
tests/test_workbook_validator.py::test_invalid_negative_or_zero_quantity PASSED          [90%]
tests/test_workbook_validator.py::test_non_numeric_quantity PASSED                        [100%]

============================= 10 passed in 13.96s =============================
```

### Verified Behaviors:
1. **All 7 Records Verified**:
   - 7 rows saved in the table in the exact order as the workbook.
   - All 5 fields (`Part`, `Qty`, `Site`, `Cost Code - SAP Budget Line`, `WBS and Project Code`) match the Excel row exactly.
2. **Trailing Dot Preservation**:
   - `2026_2.2.1.` preserves the trailing period throughout openpyxl parsing, form entry, and table DOM inspection.
3. **Strict Validation Rejection**:
   - Submitting with an omitted required field triggers an immediate `Validation Error` and does not save any row.
4. **Fail-Fast Batch Safety**:
   - Encountering an invalid row immediately halts execution and marks downstream rows as `SKIPPED`, guaranteeing no duplicate lines or ambiguous states.
5. **Dry-Run Inspection**:
   - `--dry-run` confirms all controls and validates workbook schema while leaving the table untouched (0 lines added).

---

## 7. What Remains Unverified (Production Boundaries)

As specified in the project scope, this is a local prototype only. The following production aspects are intentionally **unverified** and require review/approval before any future work:

1. **Helios PRD Live Authentication & SSO**:
   - The real portal uses enterprise SSO/OAuth or session cookies. No credentials or login flows were tested or simulated.
2. **Portal Frame / iFrame Hierarchies**:
   - Live IBM Maximo instances often embed work areas inside framesets or iframes (`iframe[name="content"]`). In the local prototype, standard top-level DOM selectors were verified.
3. **Lookup Dialog Modals in Production**:
   - The live system has magnifying glass lookup dialogs that query server-side catalogs. The automation directly enters the validated codes into the inputs. If the live portal enforces selecting strictly via the lookup popup dialog, that modal interaction will need to be mapped.
4. **Server Latency & Async Submission Handshakes**:
   - On the live portal, saving a line triggers SAP budget checks and back-end database transactions with variable latency. The prototype uses synchronous client-side state with Playwright DOM expect assertions.
5. **Work PC Environment**:
   - Browser policies, proxy settings, Python environment versions, and firewall rules on the company work PC remain unverified until the next phase.

---

## 8. Review and Sign-Off
- **Status**: Local Prototype Complete and Fully Verified.
- **Next Step**: Awaiting user review and approval before proceeding with production access planning or work-PC migration.
