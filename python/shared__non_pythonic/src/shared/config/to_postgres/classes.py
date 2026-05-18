from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TableConfig:
    id: str
    source_system: str
    source_database: str
    source_table: str
    target_table: str
    keys: List[str]
    where_clause: Optional[str]
    cadence: str  # fast | daily
    dataset: str  # logical dataset name
