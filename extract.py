import requests

from config import BACKEND_LOG_ENDPOINT, BACKEND_API_KEY, BATCH_SIZE
from datetime import datetime, timezone
from typing import Any, Iterable

from utils import _parse_dt


from log_dto import (
    AttackLogDTO,
    AttackedLogDTO,
    AssignedTasklLogDTO,
    BuffLogDTO,
    BuffedLogDTO,
    CompleteTasklLogDTO,
    CreateTasklLogDTO,
    DeadLogDTO,
    DebuffLogDTO,
    DebuffedLogDTO,
    DeleteTasklLogDTO,
    GiveItemLogDTO,
    HealLogDTO,
    HealedLogDTO,
    KillBossLogDTO,
    ReceivedItemLogDTO,
    ReviewedTasklLogDTO,
    ReviveLogDTO,
    UseItemLogDTO,
)


def fetch_logs(time_begin):
    """
    Fetch logs from backend starting after `last_id`.

    Expects BACKEND_LOG_ENDPOINT to return JSON array of log objects, each containing an `id` field.
    """
    if not BACKEND_LOG_ENDPOINT:
        raise RuntimeError("BACKEND_LOG_ENDPOINT is not set")

    headers = {}
    if BACKEND_API_KEY:
        # Be permissive about header conventions used by different backends.
        headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"
        headers["X-API-Key"] = BACKEND_API_KEY

    params = {"time_begin_raw": time_begin}

    res = requests.get(
    f"{BACKEND_LOG_ENDPOINT}/api/internal/logs?time_begin={time_begin}",
        headers=headers,
        timeout=30,
    )
    res.raise_for_status()

    data = res.json()
    return list(data["logs"])

def fetch_logs_with_max_time(time_begin):
    """
    Fetch logs and also return the max created_at timestamp found (UTC aware datetime).
    Returns: (logs: list[dict], max_created_at: datetime|None)
    """
    logs = fetch_logs(time_begin)
    max_dt = None
    if logs:
        max_dt = logs[0]["created_at"]
    return logs, max_dt

def extract_data(time_begin):
    """
    extract data to this format
    data = { "project_member_id1" : { "attack_log" : [], "create_task_log":[]  }, "project_member_id2": { "attack_log" : [], "create_task_log":[]  }}
    """
    logs = fetch_logs(time_begin)
    return build_member_log_data(logs)





def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _extract_member_id(value: Any) -> str:
    """
    Extract member ID from value, whether it's a string, dict, or other type.
    Handles cases where actor_id or other ID fields might be dictionaries instead of UUID strings.
    """
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Try common ID field names in order of preference
        return str(
            value.get("project_member_id")
            or value.get("user_id")
            or value.get("id")
            or value.get("member_id")
            or value.get("player_id")
            or value.get("receiver_id")
            or ""
        )
    # For other types (int, etc.), convert to string
    return str(value)


def _empty_member_logs() -> dict[str, list]:
    return {
        "attack_log": [],
        "attacked_log": [],
        "heal_log": [],
        "healed_log": [],
        "buff_log": [],
        "buffed_log": [],
        "debuff_log": [],
        "debuffed_log": [],
        "give_item_log": [],
        "received_item_log": [],
        "use_item_log": [],
        "kill_boss_log": [],
        "dead_log": [],
        "revive_log": [],
        "create_task_log": [],
        "delete_task_log": [],
        "complete_task_log": [],
        "assigned_task_log": [],
        "reviewed_task_log": [],
    }


def build_member_log_data(logs: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """
    Build the structure requested:
        data =
          {
            "<project_member_id>": {
               "attack_log": [AttackLogDTO, ...],
               "create_task_log": [CreateTasklLogDTO, ...],
               ...
            },
            "<project_member_id_2>": { ... },
            ...
          }
    """
    members: dict[str, dict[str, Any]] = {}

    def _ensure_member(member_id: str) -> dict[str, Any]:
        if not member_id:
            # ignore logs that can't be attributed to a member
            return {}
        if member_id not in members:
            members[member_id] = {"logs": _empty_member_logs(), "project_member": None}
        return members[member_id]

    def _set_snapshot_if_missing(member_id: str, snapshot: Any) -> None:
        if not member_id or not snapshot:
            return
        rec = _ensure_member(member_id)
        if rec and rec.get("project_member") is None and isinstance(snapshot, dict):
            rec["project_member"] = snapshot

    for log in logs:
        if not isinstance(log, dict):
            continue
        event_type = log.get("event_type")
        project_id = log.get("project_id")
        actor_id = _extract_member_id(log.get("actor_id"))  # project_member_id for user events
        payload = (log.get("payload") or {}) if isinstance(log.get("payload"), dict) else {}

        created_at = _parse_dt(log.get("created_at"))

        # ---------- Combat ----------
        if event_type == "USER_ATTACK":
            member_id = actor_id
            dto = AttackLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                damage=_to_int(payload.get("damage")),
                score_receive=_to_int(payload.get("score_receive") or payload.get("score_recieve")),
                boss_hp=_to_int(payload.get("boss_hp")),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["attack_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("actor"))
            continue

        if event_type == "BOSS_ATTACK":
            # receiver side (player attacked)
            member_id = _extract_member_id(
                payload.get("player_id")
                or payload.get("receiver_id")
                or payload.get("target_player_id")
            )
            dto = AttackedLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                damage=_to_int(payload.get("damage")),
                player_hp=_to_int(payload.get("player_hp")),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["attacked_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("player") or payload.get("receiver") or payload.get("target"))
            continue

        # ---------- Heal ----------
        if event_type == "HEAL":
            healer_id = actor_id
            receiver_id = _extract_member_id(payload.get("receiver_id") or payload.get("player_id"))

            # healer-side log
            healer_dto = HealLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=healer_id,
                event_type=str(event_type),
                score_receive=_to_int(payload.get("score_receive") or payload.get("score_recieve")),
                heal_amount=_to_int(payload.get("heal_amount")),
                created_at=created_at,
            )
            rec = _ensure_member(healer_id)
            if rec:
                rec["logs"]["heal_log"].append(healer_dto)
            _set_snapshot_if_missing(healer_id, payload.get("actor"))

            # receiver-side log
            if receiver_id:
                healed_dto = HealedLogDTO(
                    project_id=str(project_id) if project_id else "",
                    project_member_id=receiver_id,
                    event_type=str(event_type),
                    heal_amount=_to_int(payload.get("heal_amount")),
                    player_hp=str(payload.get("player_hp") or ""),
                    created_at=created_at,
                )
                rec2 = _ensure_member(receiver_id)
                if rec2:
                    rec2["logs"]["healed_log"].append(healed_dto)
                _set_snapshot_if_missing(receiver_id, payload.get("receiver") or payload.get("player"))
            continue

        # ---------- Effects (buff/debuff) ----------
        if event_type in ("APPLY_BUFF", "APPLY_DEBUFF"):
            effect = payload.get("effect") or {}
            effect_type = (effect.get("effect_type") or effect.get("type") or "")
            effect_value = _to_int(effect.get("effect_value") or effect.get("value"))

            applier_id = actor_id
            receiver_id = _extract_member_id(payload.get("receiver_id"))

            if event_type == "APPLY_BUFF":
                applier_dto = BuffLogDTO(
                    project_id=str(project_id) if project_id else "",
                    project_member_id=applier_id,
                    event_type=str(event_type),
                    score_receive=_to_int(payload.get("score_receive") or payload.get("score_recieve")),
                    buff_amount=effect_value,
                    buff_type=str(effect_type),
                    created_at=created_at,
                )
                rec = _ensure_member(applier_id)
                if rec:
                    rec["logs"]["buff_log"].append(applier_dto)
                _set_snapshot_if_missing(applier_id, payload.get("actor"))

                if receiver_id:
                    recv_dto = BuffedLogDTO(
                        project_id=str(project_id) if project_id else "",
                        project_member_id=receiver_id,
                        event_type=str(event_type),
                        buff_amount=effect_value,
                        buff_type=str(effect_type),
                        created_at=created_at,
                    )
                    rec2 = _ensure_member(receiver_id)
                    if rec2:
                        rec2["logs"]["buffed_log"].append(recv_dto)
                    _set_snapshot_if_missing(receiver_id, payload.get("receiver"))

            else:
                applier_dto = DebuffLogDTO(
                    project_id=str(project_id) if project_id else "",
                    project_member_id=applier_id,
                    event_type=str(event_type),
                    score_receive=_to_int(payload.get("score_receive") or payload.get("score_recieve")),
                    debuff_amount=effect_value,
                    debuff_type=str(effect_type),
                    created_at=created_at,
                )
                rec = _ensure_member(applier_id)
                if rec:
                    rec["logs"]["debuff_log"].append(applier_dto)
                _set_snapshot_if_missing(applier_id, payload.get("actor"))

                if receiver_id:
                    recv_dto = DebuffedLogDTO(
                        project_id=str(project_id) if project_id else "",
                        project_member_id=receiver_id,
                        event_type=str(event_type),
                        debuff_amount=effect_value,
                        debuff_type=str(effect_type),
                        created_at=created_at,
                    )
                    rec2 = _ensure_member(receiver_id)
                    if rec2:
                        rec2["logs"]["debuffed_log"].append(recv_dto)
                    _set_snapshot_if_missing(receiver_id, payload.get("receiver"))

            continue

        # ---------- Items ----------
        if event_type == "GIVE_ITEM":
            giver_id = actor_id
            receiver_id = _extract_member_id(payload.get("receiver_id"))
            item = payload.get("item") or {}
            effect = payload.get("effect") or {}
            item_name = item.get("item_name") or item.get("name") or ""
            item_effect_type = effect.get("effect_type") or ""
            item_rare_level = item.get("item_rare_level") or item.get("rare_level") or ""

            giver_dto = GiveItemLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=giver_id,
                event_type=str(event_type),
                item_name=str(item_name),
                item_effect_type=str(item_effect_type),
                item_rare_level=str(item_rare_level),
                score_receive=_to_int(payload.get("score_receive") or payload.get("score_recieve")),
                created_at=created_at,
            )
            rec = _ensure_member(giver_id)
            if rec:
                rec["logs"]["give_item_log"].append(giver_dto)
            _set_snapshot_if_missing(giver_id, payload.get("actor"))

            if receiver_id:
                recv_dto = ReceivedItemLogDTO(
                    project_id=str(project_id) if project_id else "",
                    project_member_id=receiver_id,
                    event_type=str(event_type),
                    item_name=str(item_name),
                    item_effect_type=str(item_effect_type),
                    item_rare_level=str(item_rare_level),
                    created_at=created_at,
                )
                rec2 = _ensure_member(receiver_id)
                if rec2:
                    rec2["logs"]["received_item_log"].append(recv_dto)
            continue

        if event_type == "USE_ITEM":
            user_id = actor_id
            item = payload.get("item") or {}
            effect = payload.get("effect") or {}
            item_name = item.get("item_name") or item.get("name") or ""
            item_effect_type = effect.get("effect_type") or ""
            item_rare_level = item.get("item_rare_level") or item.get("rare_level") or ""
            dto = UseItemLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=user_id,
                event_type=str(event_type),
                item_name=str(item_name),
                item_effect_type=str(item_effect_type),
                item_rare_level=str(item_rare_level),
                created_at=created_at,
            )
            rec = _ensure_member(user_id)
            if rec:
                rec["logs"]["use_item_log"].append(dto)
            continue

        # ---------- Progression / revive ----------
        if event_type == "KILL_BOSS":
            member_id = actor_id
            dto = KillBossLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["kill_boss_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("actor"))
            continue

        if event_type == "KILL_PLAYER":
            member_id = _extract_member_id(payload.get("receiver_id"))
            dto = DeadLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["dead_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("receiver") or payload.get("player"))
            continue

        if event_type in ("USER_REVIVE", "BOSS_REVIVE"):
            member_id = actor_id if actor_id else _extract_member_id(payload.get("player_id"))
            dto = ReviveLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["revive_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("actor"))
            continue

        # ---------- Task lifecycle ----------
        if event_type == "TASK_CREATED":
            member_id = actor_id
            task = payload.get("task") or {}
            task_id = str(task.get("task_id")) or ""
            task_name = str(task.get("task_name")) or ""
            task_priority = task.get("priority") or ""
            task_deadline = task.get("deadline") or ""
            task_created_at_raw = (task.get("created_at")) or ""
            dto = CreateTasklLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                task_id=task_id,
                task_name=task_name,
                task_priority=task_priority,
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["create_task_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("actor"))
            continue

        if event_type == "TASK_DELETED":
            member_id = actor_id
            task = payload.get("task") or {}
            task_id = str(task.get("task_id")) or ""
            task_name = str(task.get("task_name")) or ""
            task_priority = task.get("priority") or ""
            task_deadline = task.get("deadline") or ""
            task_created_at_raw = (task.get("created_at")) or ""
            dto = DeleteTasklLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                task_created_at=_parse_dt(task_created_at_raw),
                task_id=task_id,
                task_name=task_name,
                task_priority=task_priority,
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["delete_task_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("actor"))
            continue

        if event_type == "TASK_COMPLETED":
            member_id = actor_id
            task = payload.get("task") or {}
            task_id = str(task.get("task_id")) or ""
            task_name = str(task.get("task_name")) or ""
            task_priority = task.get("priority") or ""
            task_deadline = task.get("deadline") or ""
            task_created_at_raw = (task.get("created_at")) or ""
            dto = CompleteTasklLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                task_created_at=_parse_dt(task_created_at_raw),
                task_id=task_id,
                task_name=task_name,
                task_priority=task_priority,
                deadline=payload.get("deadline"),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["complete_task_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("actor"))
            continue

        if event_type == "ASSIGN_USER":
            # receiver_id is
            member_id = _extract_member_id(payload.get("receiver_id"))
            task = payload.get("task") or {}
            task_id = str(task.get("task_id")) or ""
            task_name = str(task.get("task_name")) or ""
            task_priority = task.get("priority") or ""
            task_deadline = task.get("deadline") or ""
            task_created_at_raw = (task.get("created_at"))  or ""
            dto = AssignedTasklLogDTO(
                project_id=str(project_id) if project_id else "",
                project_member_id=member_id,
                event_type=str(event_type),
                task_created_at=_parse_dt(task_created_at_raw),
                task_id=task_id,
                task_name=task_name,
                task_priority=task_priority,
                deadline=_parse_dt(task_deadline),
                created_at=created_at,
            )
            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["assigned_task_log"].append(dto)
            _set_snapshot_if_missing(member_id, payload.get("receiver_id"))
            continue

        if event_type == "TASK_REVIEW":
            # Store under receiver (the member being reviewed)
            receiver = payload.get("receiver") or {}
            member_id = _extract_member_id(payload.get("receiver_id") or receiver.get("project_member_id"))
            if not member_id:
                continue

            # Payload can be either:
            #  - log payload: {task_id, task, receiver_id, actor, receiver, sentiment_score}
            #  - API-like payload: {report: {task: {...}, sentiment_score, created_at}, reviewer, receiver}
            report = payload.get("report") or {}
            task = report.get("task") if isinstance(report.get("task"), dict) else payload.get("task") or {}

            task_id = str(task.get("task_id") or payload.get("task_id") or "") if isinstance(task, dict) else ""
            task_name = str(task.get("task_name") or task.get("name") or "") if isinstance(task, dict) else ""
            task_priority = _to_int(task.get("priority") if isinstance(task, dict) else None)
            sentiment_score = float(
                (report.get("sentiment_score") if isinstance(report, dict) else None)
                or payload.get("sentiment_score")
                or 0
            )

            deadline_raw = task.get("deadline") if isinstance(task, dict) else None
            task_created_at_raw = task.get("created_at") if isinstance(task, dict) else None
            created_at_raw = (report.get("created_at") if isinstance(report, dict) else None) or created_at

            # User note: sometimes "project_id" is effectively the receiver id in this structure.
            # Prefer real project_id if present; fallback to receiver member id.
            dto_project_id = str(project_id) if project_id else member_id

            dto = ReviewedTasklLogDTO(
                project_id=dto_project_id,
                project_member_id=member_id,
                event_type=str(event_type),
                task_id=task_id,
                task_name=task_name,
                task_priority=task_priority,
                sentiment_score=sentiment_score,
                task_created_at=_parse_dt(task_created_at_raw),
                deadline=_parse_dt(deadline_raw),
                created_at=_parse_dt(created_at_raw),
            )

            rec = _ensure_member(member_id)
            if rec:
                rec["logs"]["reviewed_task_log"].append(dto)
            _set_snapshot_if_missing(member_id, receiver or payload.get("receiver_id"))
            continue

    # Return a single mapping keyed by project_member_id -> logs dict
    return {member_id: rec["logs"] for member_id, rec in members.items()}
