from __future__ import annotations


from collections import Counter, defaultdict
from statistics import mean

from task_classifier import build_default_task_classifier

_CLF = None


def _get_clf():
    global _CLF
    if _CLF is not None:
        return _CLF
    _CLF = build_default_task_classifier()
    return _CLF


def frequecy_task_calculate(logs):
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

def work_quality_calculate(logs):
    try:
        reviewed_logs = logs.get("reviewed_task_log") or []
        if not reviewed_logs:
            return None, {}, None, None

        task_names = []
        sentiments = []

        for l in reviewed_logs:
            task_name = getattr(l, "task_name", None)
            score = getattr(l, "sentiment_score", None)
            if not task_name or score is None:
                continue
            task_names.append(str(task_name))
            sentiments.append(float(score))

        if not task_names:
            return None, {}, None, None

        clf = _get_clf()
        preds = clf.predict_top1(task_names)

        category_scores = defaultdict(list)
        for idx, p in enumerate(preds):
            if isinstance(p, dict) and p.get("label"):
                category_scores[str(p["label"])].append(sentiments[idx])

        if not sentiments:
            return None, {}, None, None

        overall_avg_sentiment = mean(sentiments)

        category_avg_sentiment = {
            cat: (sum(vals) / len(vals)) for cat, vals in category_scores.items() if vals
        }

        best_category = None
        best_avg = 0.0
        if category_avg_sentiment:
            best_category, best_avg = max(category_avg_sentiment.items(), key=lambda kv: kv[1])

        return float(overall_avg_sentiment), category_avg_sentiment, best_category, float(best_avg)

    except Exception:
        return None, {}, None, None