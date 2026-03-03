from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class TaskClassifierConfig:
    """
    Zero-shot task classifier (Transformers).

    You can point `model_id_or_path` to:
      - a HuggingFace model id (downloads at runtime), or
      - a local directory (pre-downloaded snapshot)
    """

    model_id_or_path: str
    labels: Sequence[str]
    multi_label: bool = False


DEFAULT_TASK_CLASSIFIER_MODEL = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"

# Labels from AI-Component task classification v3.
DEFAULT_TASK_CLASSIFIER_LABELS: list[str] = [
    "Conducting Research",
    "Creating Content and Visuals",
    "Task Assignment and Scheduling",
    "Programming",
    "Working with Spreadsheets and Data",
    "Reviewing and Providing Feedback",
    "Documentation",
    "Testing",
    "Translation",
    "Sending Emails and Communication",
    "Finalizing and Submitting Work",
]


class ZeroShotTaskClassifier:
    def __init__(self, cfg: TaskClassifierConfig):
        self._cfg = cfg
        self._pipe = None

    def _get_pipe(self):
        if self._pipe is not None:
            return self._pipe

        try:
            from transformers import pipeline  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "transformers is not installed. Add it to ETL requirements, "
                "or only use the task classifier in a separate service."
            ) from e

        self._pipe = pipeline("zero-shot-classification", model=self._cfg.model_id_or_path)
        return self._pipe

    def predict_top1(self, texts: Iterable[str]) -> list[dict[str, Any]]:
        """
        Returns list of {label, score} per text.
        """
        pipe = self._get_pipe()

        texts_list = [str(t) for t in texts]
        if not texts_list:
            return []

        # HuggingFace pipelines support batching with list input; this is much faster than per-row calls.
        res_all = pipe(texts_list, list(self._cfg.labels), multi_label=self._cfg.multi_label)
        if isinstance(res_all, dict):
            res_all = [res_all]

        out: list[dict[str, Any]] = []
        for res in res_all:
            out.append({"label": res["labels"][0], "score": float(res["scores"][0])})
        return out


def build_default_task_classifier() -> ZeroShotTaskClassifier:
    """
    Constant config (no env vars).

    Note: this still requires `transformers` (and typically `torch`) at runtime
    when you actually call `predict_top1(...)`.
    """
    return ZeroShotTaskClassifier(
        TaskClassifierConfig(
            model_id_or_path=DEFAULT_TASK_CLASSIFIER_MODEL,
            labels=DEFAULT_TASK_CLASSIFIER_LABELS,
        )
    )


