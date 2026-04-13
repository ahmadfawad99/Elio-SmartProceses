from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

try:
    from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover - optional at runtime until deps are installed
    IsolationForest = None

from shared.enums import Severity
from shared.schemas import AnomalyEvent, MetricPointIn

from .features import MetricFeatures, extract_metric_features


class AnomalyDetector:
    def __init__(self) -> None:
        self._model = (
            IsolationForest(
                n_estimators=100,
                contamination=0.15,
                random_state=42,
            )
            if IsolationForest is not None
            else None
        )

    def detect(self, metrics: list[MetricPointIn]) -> AnomalyEvent:
        latest = metrics[-1]
        features = extract_metric_features(metrics)

        anomaly_score = self._score(metrics)
        severity = self._severity_from_score(anomaly_score, features.temperature_max)
        summary = self._summary(severity, features)
        reasoning = self._reasoning(features, anomaly_score)

        return AnomalyEvent(
            machine_id=latest.machine_id,
            severity=severity,
            anomaly_score=round(anomaly_score, 3),
            anomaly_type="multivariate_infra_anomaly",
            summary=summary,
            detected_at=datetime.now(timezone.utc),
            context={
                "cpu_mean": round(features.cpu_mean, 2),
                "cpu_max": round(features.cpu_max, 2),
                "memory_mean": round(features.memory_mean, 2),
                "temperature_mean": round(features.temperature_mean, 2),
                "temperature_max": round(features.temperature_max, 2),
                "cpu_trend": round(features.cpu_trend, 3),
                "temp_trend": round(features.temp_trend, 3),
                "pressure_index": round(features.pressure_index, 2),
                "window_size": len(metrics),
            },
            reasoning=reasoning,
        )

    def _score(self, metrics: list[MetricPointIn]) -> float:
        features = extract_metric_features(metrics)
        vector = features.as_vector().reshape(1, -1)

        if self._model is not None and len(metrics) >= 8:
            training_rows = self._build_training_rows(metrics)
            if len(training_rows) >= 8:
                self._model.fit(training_rows)
                raw_score = -float(self._model.score_samples(vector)[0])
                normalized = 1 / (1 + np.exp(-raw_score * 4))
                return float(np.clip(normalized, 0.0, 1.0))

        heuristic = (
            (features.cpu_max / 100) * 0.25
            + (features.memory_max / 100) * 0.20
            + min(features.temperature_max / 100, 1.2) * 0.35
            + min(abs(features.cpu_trend) / 10, 1.0) * 0.10
            + min(abs(features.temp_trend) / 5, 1.0) * 0.10
        )
        return float(np.clip(heuristic, 0.0, 1.0))

    def _build_training_rows(self, metrics: list[MetricPointIn]) -> np.ndarray:
        rows: list[np.ndarray] = []
        for index in range(4, len(metrics) + 1):
            window = metrics[max(0, index - 5) : index]
            rows.append(extract_metric_features(window).as_vector())
        return np.vstack(rows) if rows else np.empty((0, 11))

    def _severity_from_score(self, score: float, temperature_max: float) -> Severity:
        if score >= 0.90 or temperature_max >= 88:
            return Severity.critical
        if score >= 0.75 or temperature_max >= 82:
            return Severity.high
        if score >= 0.55:
            return Severity.medium
        return Severity.low

    def _summary(self, severity: Severity, features: MetricFeatures) -> str:
        if severity in {Severity.high, Severity.critical}:
            return "Thermal and utilization signals indicate unstable machine behavior."
        return "Machine shows emerging deviation from recent operating baseline."

    def _reasoning(self, features: MetricFeatures, score: float) -> str:
        return (
            "The anomaly score blends utilization peaks, temperature spikes, and short-term trend "
            f"acceleration. Current window shows CPU max {features.cpu_max:.1f}%, memory max "
            f"{features.memory_max:.1f}%, temperature max {features.temperature_max:.1f}C, "
            f"with pressure index {features.pressure_index:.1f} and normalized anomaly score {score:.2f}."
        )


anomaly_detector = AnomalyDetector()
