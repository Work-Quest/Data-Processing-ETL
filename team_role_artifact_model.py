from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import joblib
import pandas as pd


@dataclass(frozen=True)
class TeamRoleArtifactPaths:
    """
    Local, MLflow-free artifact layout.

    Expected files (copied from AI-Component artifacts or MLflow artifacts):
      - kmeans_model.pkl
      - scaler.pkl
      - role_mapping.json
      - feature_names.json
    """

    root_dir: str

    @property
    def kmeans_model(self) -> str:
        return os.path.join(self.root_dir, "kmeans_model.pkl")

    @property
    def scaler(self) -> str:
        return os.path.join(self.root_dir, "scaler.pkl")

    @property
    def role_mapping(self) -> str:
        return os.path.join(self.root_dir, "role_mapping.json")

    @property
    def feature_names(self) -> str:
        return os.path.join(self.root_dir, "feature_names.json")


class TeamRoleArtifactModel:
    """
    Lightweight inference wrapper compatible with the model trained in:
      AI-Component/mlflow/role_categorization/role_categorization_v3.py
    but without requiring an MLflow tracking server at runtime.
    """

    def __init__(self, *, artifact_dir: str):
        self._paths = TeamRoleArtifactPaths(os.path.abspath(artifact_dir))
        self._kmeans = None
        self._scaler = None
        self._role_mapping: dict[str, str] | dict[int, str] | None = None
        self._feature_names: list[str] | None = None

    def _load(self) -> None:
        if self._kmeans is not None:
            return

        if not os.path.isdir(self._paths.root_dir):
            raise FileNotFoundError(f"Artifact directory not found: {self._paths.root_dir}")

        for p in (self._paths.kmeans_model, self._paths.scaler, self._paths.role_mapping, self._paths.feature_names):
            if not os.path.exists(p):
                raise FileNotFoundError(f"Missing artifact file: {p}")

        self._kmeans = joblib.load(self._paths.kmeans_model)
        self._scaler = joblib.load(self._paths.scaler)
        with open(self._paths.role_mapping, "r", encoding="utf-8") as f:
            self._role_mapping = json.load(f)
        with open(self._paths.feature_names, "r", encoding="utf-8") as f:
            self._feature_names = json.load(f)

    def predict_roles(self, rows: Sequence[Mapping[str, Any]]) -> list[str]:
        """
        rows must include the same keys as feature_names.json (typically):
          - avg_workload
          - team_work
          - work_speed
          - overall_quality_score
        """
        self._load()
        assert self._feature_names is not None
        assert self._role_mapping is not None
        assert self._scaler is not None
        assert self._kmeans is not None

        df = pd.DataFrame(list(rows))
        missing = [c for c in self._feature_names if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")

        X = df[self._feature_names].values
        X_scaled = self._scaler.transform(X)
        clusters = self._kmeans.predict(X_scaled)

        # role_mapping might have int keys (python dict) or str keys (json)
        roles: list[str] = []
        for c in clusters:
            role = self._role_mapping.get(c)
            if role is None:
                role = self._role_mapping.get(str(int(c)))  # type: ignore[arg-type]
            roles.append(role or "Unknown")
        return roles





