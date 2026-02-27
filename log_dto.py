from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LogDTO:
    id: str
    project_id : str
    project_member_id: str
    event_type: int
    payload: dict


