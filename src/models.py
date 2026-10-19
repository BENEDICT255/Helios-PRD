"""
Data models for Material Line entry and run reports.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class MaterialLineRecord:
    row_index: int
    item_code: str
    quantity: int
    site_id: str
    cost_code: str  # Excel "Line" -> Page "Cost Code - SAP Budget Line"
    wbs: str        # Excel "WBS" -> Page "WBS and Project Code"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_index": self.row_index,
            "item_code": self.item_code,
            "quantity": self.quantity,
            "site_id": self.site_id,
            "cost_code": self.cost_code,
            "wbs": self.wbs,
        }

@dataclass
class RowResult:
    row_index: int
    item_code: str
    quantity: int
    site_id: str
    cost_code: str
    wbs: str
    status: str  # "SUCCESS", "FAILED", "SKIPPED", "DRY_RUN"
    saved_line_no: Optional[int] = None
    verification_passed: bool = False
    error_message: Optional[str] = None
    verified_values: Optional[Dict[str, Any]] = None

@dataclass
class RunReport:
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    workbook_path: str = ""
    target_url: str = ""
    is_dry_run: bool = False
    total_rows: int = 0
    successful_rows: int = 0
    failed_rows: int = 0
    skipped_rows: int = 0
    stop_reason: Optional[str] = None
    row_results: List[RowResult] = field(default_factory=list)

    def finalize(self):
        self.end_time = datetime.now().isoformat()
        self.successful_rows = sum(1 for r in self.row_results if r.status == "SUCCESS")
        self.failed_rows = sum(1 for r in self.row_results if r.status == "FAILED")
        self.skipped_rows = sum(1 for r in self.row_results if r.status == "SKIPPED")
