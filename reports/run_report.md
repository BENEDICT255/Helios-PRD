# Helios PRD - Material Lines Entry Automation Report

## Summary
- **Timestamp**: `2026-10-19T11:06:19.769776` to `2026-10-19T11:06:36.179691`
- **Target URL**: `http://127.0.0.1:8000/index.html`
- **Workbook**: `C:\Users\surface laptop\Downloads\Material PRD\data\sample_material_lines.xlsx`
- **Mode**: `LIVE RUN`
- **Total Rows**: `7`
- **Successfully Saved & Verified**: `7`
- **Failed / Rejected**: `0`
- **Skipped**: `0`

## Detailed Row-by-Row Execution

| Excel Row | Part (Item Code) | Qty | Site | Cost Code - SAP Budget Line | WBS and Project Code | Saved Line # | Status | Verification | Error Details |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| 2 | `CABL00058` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 10 | ✅ SUCCESS | ✅ Matched All 5 | - |
| 3 | `CABL00059` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 20 | ✅ SUCCESS | ✅ Matched All 5 | - |
| 4 | `DBDS00031` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 30 | ✅ SUCCESS | ✅ Matched All 5 | - |
| 5 | `DBDS00030` | 2 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 40 | ✅ SUCCESS | ✅ Matched All 5 | - |
| 6 | `DBDS00029` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 50 | ✅ SUCCESS | ✅ Matched All 5 | - |
| 7 | `DBDS00028` | 2 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 60 | ✅ SUCCESS | ✅ Matched All 5 | - |
| 8 | `FOKT00004` | 1 | `TZKA8027` | `2026_2.2.1.` | `TZKA8027-1795051262` | 70 | ✅ SUCCESS | ✅ Matched All 5 | - |

## Exact Value Verification Verification Notes
- Excel `Line` value `2026_2.2.1.` must preserve the trailing period in the page `Cost Code - SAP Budget Line`.
- No save retry occurs on uncertain or failed status to prevent duplicates.
- Missing required fields or invalid quantities halt the batch immediately.
