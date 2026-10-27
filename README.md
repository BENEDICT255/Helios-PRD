# Helios PRD Material Line Entry

This Windows desktop tool reads the five required values from Excel, fills the matching fields in the open Site Material Request, and presses **Enter once per row**. You review the Lines grid and continue the remaining PRD process manually.

## What PRD mode does

- Uses the five input `name` attributes copied from the actual PRD page:
  - Part: `wspf_10_mll_udfchar03`
  - Qty: `wspf_10_mll_udfnum01`
  - Site: `wspf_10_mll_udfchar05`
  - Cost Code / SAP Budget Line: `wspf_10_mll_udfchar09`
  - WBS and Project Code: `wspf_10_mll_udfchar16`
- Checks that one visible, editable set of those inputs is present.
- Fills the five values, checks that the visible input values match Excel, then presses Enter on WBS.
- Waits for all five inputs to clear before continuing. If they do not clear, it stops and marks the row **uncertain**.
- Does not inspect the Lines grid, click the floppy-disk icon, verify a server save, or retry a row. **Enter sent is not proof that PRD saved the line.**
- Does not log in or store credentials. You sign in to the Chrome session yourself.

The live portal has not been directly accessible from this development environment. The first live test must use one row on the test request, then you must review the result in PRD before using a larger workbook. Lookup behavior and the page's Enter/reset behavior are confirmed only by that real one-row test.

## Work PC setup

1. Extract this ZIP to a normal folder, for example `C:\Users\<you>\PycharmProjects\Helios-PRD-copy`.
2. Run `setup_work_pc.bat`. It uses the Python launcher when available, installs the dependencies in `.venv`, and installs Playwright Chromium. If company network controls block installation, ask IT to allow the required Python package and browser downloads.
3. Run `run_tests.bat`. Continue only if every test passes.
4. Run `run_launcher.bat` to open the desktop launcher.

## Prepare and pilot the Excel workbook

1. In the launcher, choose **Download Blank Excel Template** and save it.
2. Enter values starting on row 2. Do not rename the five column headers.
3. Make a copy containing only the first intended material row for the initial live pilot. Save it as a separate workbook so the full list stays unchanged.
4. Check the item code, quantity, site, Line, and WBS against the request before running. Quantity must be a positive whole number. Text such as `2026_2.2.1.` is preserved, including the final period.

## Test on the PRD request

1. Double-click `start_chrome_sso.bat`.
2. In the Chrome window it opens, sign in to Helios PRD, open the test Site Material Request, select **Lines**, and leave the five fields blank.
3. Copy the URL from that tab.
4. In the launcher, select **Browse Excel** and choose the one-row pilot workbook.
5. Select **Attach to Chrome / PRD** and paste the copied URL.
6. Click **Dry-Run Validation** first. This checks that the five fields are present and does not type or submit anything.
7. If dry run passes, click **Run Automation** and confirm the prompt. Keep the PRD tab open and do not interact with the fields while it runs.
8. Review the Lines grid yourself. Confirm every value and that the line appeared once. If the input fields did not clear or the launcher reports an uncertain row, inspect the request manually and do not rerun that row.
9. After the one-row pilot works, prepare the intended full workbook and use the same steps on the intended request.

## Local demo

Choose **Local Demo Page** in the launcher to test the Excel workflow against the bundled dummy page. The demo is not connected to PRD. It checks the saved rows in the demo table; those checks do not establish that PRD behaves the same way.

## Reports

Each run writes `reports/run_report.md` and `reports/run_report.json`.

- Demo entries are labelled saved and verified by the dummy page.
- PRD entries are labelled **Enter sent — review**. The report does not claim that PRD saved them.
- A row is labelled **uncertain** if Enter was sent but the five input fields did not return to blank. Review it before retrying.

## Project files

- `launcher.py`: desktop UI and Excel selection.
- `src/automation.py`: demo automation and PRD field entry.
- `src/excel_reader.py`: workbook validation.
- `src/template_generator.py`: clean Excel template.
- `tests/`: workbook, demo, and mock-PRD behavior tests.
- `web/`: local-only dummy page.
