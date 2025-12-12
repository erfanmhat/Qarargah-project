from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FieldError:
    sheet: str
    section: str
    field: str
    message: str
    cell: Optional[str] = None
    value: Any = None


@dataclass
class ParsedLeave:
    leave_type: str
    start_date: str
    end_date: str
    notes: str = ""


@dataclass
class ParsedReduction:
    reduction_type_title: str
    days: int


@dataclass
class ParsedSoldierSheet:
    sheet_name: str
    soldier: Dict[str, Any] = field(default_factory=dict)
    leaves: List[ParsedLeave] = field(default_factory=list)
    reductions: List[ParsedReduction] = field(default_factory=list)


@dataclass
class ImportPreview:
    token: str
    items: List[ParsedSoldierSheet]
    errors: List[FieldError]
