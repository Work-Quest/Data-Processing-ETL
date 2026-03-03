from __future__ import annotations

from collections import Counter
from typing import Any, Tuple

from task_classifier import build_default_task_classifier

_CLF = None


def _get_clf():
    global _CLF
    if _CLF is not None:
        return _CLF
    _CLF = build_default_task_classifier()
    return _CLF


def strength_calculate(logs):
    """
    Classify each assigned task's task_name, then return:
      - most_common_category
      - count_amount (how many tasks in that category)
    """
    try:
        assigned_logs = logs.get("assigned_task_log") or []
        if not assigned_logs:
            return None, 0

        task_names: list[str] = []
        for l in assigned_logs:
            task_name = getattr(l, "task_name", None) or getattr(l, "name", None)
            if task_name:
                task_names.append(str(task_name))

        if not task_names:
            return None, 0

        clf = _get_clf()
        preds = clf.predict_top1(task_names)  # list[{label, score}]
        labels = [p.get("label") for p in preds if isinstance(p, dict) and p.get("label")]
        if not labels:
            return None, 0

        counts = Counter(labels)
        strength, count_amount = counts.most_common(1)[0]
        print(strength, count_amount)
        return str(strength), int(count_amount)
    except Exception:
        # Don't let classifier failures break ETL
        return None, 0