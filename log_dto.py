from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping


# @dataclass(frozen=True)
# class LogDTO:
#     id: str
#     project_id : str
#     project_member_id: str
#     event_type: int
#     payload: dict
#


@dataclass(frozen=True)
class AttackLogDTO:
    project_id : str
    project_member_id: str
    event_type: str
    damage: int
    score_receive: int
    boss_hp: int
    created_at: datetime

@dataclass(frozen=True)
class AttackedLogDTO:
    project_id : str
    project_member_id: str
    event_type: str
    damage: int
    player_hp: int
    created_at: datetime


@dataclass(frozen=True)
class HealLogDTO:
    project_id : str
    project_member_id: str
    event_type: str
    score_receive: int
    heal_amount: int
    created_at: datetime


@dataclass(frozen=True)
class HealedLogDTO:
    project_id : str
    project_member_id: str
    event_type: str
    heal_amount: int
    player_hp: str
    created_at: datetime


@dataclass(frozen=True)
class BuffLogDTO:
    project_id : str
    project_member_id: str
    event_type: str
    score_receive: int
    buff_amount: int
    buff_type: str
    created_at: datetime


@dataclass(frozen=True)
class BuffedLogDTO:
    project_id : str
    project_member_id: str
    event_type: str
    buff_amount: int
    buff_type: str
    created_at: datetime



@dataclass(frozen=True)
class DebuffLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    score_receive: int
    debuff_amount: int
    debuff_type: str
    created_at: datetime

@dataclass(frozen=True)
class DebuffedLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    debuff_amount: int
    debuff_type: str
    created_at: datetime

@dataclass(frozen=True)
class GiveItemLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    item_name: str
    item_effect_type: str
    item_rare_level: str
    score_receive: int
    created_at: datetime

@dataclass(frozen=True)
class ReceivedItemLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    item_name: str
    item_effect_type: str
    item_rare_level: str
    created_at: datetime

@dataclass(frozen=True)
class UseItemLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    item_name: str
    item_effect_type: str
    item_rare_level: str
    created_at: datetime

@dataclass(frozen=True)
class KillBossLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    created_at: datetime

@dataclass(frozen=True)
class DeadLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    created_at: datetime

@dataclass(frozen=True)
class ReviveLogDTO:
    project_id: str
    project_member_id: str
    event_type: str
    created_at: datetime

@dataclass(frozen=True)
class CreateTasklLogDTO:
    project_id : str
    project_member_id: str
    event_type: int
    task_id : str
    task_name: str
    task_priority: int
    created_at: datetime

@dataclass(frozen=True)
class DeleteTasklLogDTO:
    project_id : str
    project_member_id: str
    event_type: int
    task_created_at: datetime
    task_id : str
    task_name: str
    task_priority: int
    created_at: datetime

@dataclass(frozen=True)
class CompleteTasklLogDTO:
    project_id : str
    project_member_id: str
    event_type: int
    task_id : str
    task_name: str
    task_priority: int
    task_created_at: datetime
    deadline: datetime
    created_at: datetime

@dataclass(frozen=True)
class AssignedTasklLogDTO:
    project_id : str
    project_member_id: str
    event_type: int
    task_id : str
    task_name: str
    task_priority: int
    task_created_at: datetime
    deadline: datetime
    created_at: datetime

@dataclass(frozen=True)
class ReviewedTasklLogDTO:
    project_id : str
    project_member_id: str
    event_type: int
    task_id : str
    task_name: str
    task_priority: int
    sentiment_score: float
    task_created_at: datetime
    deadline: datetime
    created_at: datetime