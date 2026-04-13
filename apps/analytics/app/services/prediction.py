from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from shared.schemas import MetricPointIn, PredictionEvent

from .features import MetricFeatures, extract_metric_features


class FailurePredictor:
    def predict(self, metrics: list[MetricPointIn]) -> PredictionEvent:
        latest = metrics[-1]
        features = extract_metric_features(metrics)
        risk_score = self._risk_score(features)
        time_to_failure = self._time_to_failure_minutes(risk_score, features.temp_trend)
        failure_type = self._failure_type(features)

        return PredictionEvent(
            machine_id=latest.machine_id,
            risk_score=risk_score,
            prediction_type="predictive_maintenance",
            failure_type=failure_type,
            time_to_failure_minutes=time_to_failure,
            generated_at=datetime.now(timezone.utc),
            features={
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
            reasoning=self._reasoning(features, risk_score, time_to_failure, failure_type),
        )

    def _risk_score(self, features: MetricFeatures) -> float:
        linear = (
            (features.cpu_mean / 100) * 0.22
            + (features.cpu_max / 100) * 0.12
            + (features.memory_mean / 100) * 0.18
            + min(features.temperature_mean / 90, 1.2) * 0.18
            + min(features.temperature_max / 90, 1.3) * 0.18
            + min(max(features.cpu_trend, 0.0) / 8, 1.0) * 0.05
            + min(max(features.temp_trend, 0.0) / 3, 1.0) * 0.07
        )
        nonlinear = 1 / (1 + np.exp(-(linear * 4 - 2)))
        return round(float(np.clip(nonlinear, 0.01, 0.99)), 3)

    def _time_to_failure_minutes(self, risk_score: float, temp_trend: float) -> int:
        urgency_multiplier = max(0.35, 1 - risk_score)
        trend_penalty = max(0.5, 1 - max(temp_trend, 0) / 10)
        return max(5, int(180 * urgency_multiplier * trend_penalty))

    def _failure_type(self, features: MetricFeatures) -> str:
        if features.temperature_max >= 85 or features.temp_trend > 1.5:
            return "thermal_overload"
        if features.memory_mean >= 85:
            return "memory_exhaustion"
        if features.cpu_mean >= 88:
            return "compute_saturation"
        return "general_resource_degradation"

    def _reasoning(
        self,
        features: MetricFeatures,
        risk_score: float,
        time_to_failure: int,
        failure_type: str,
    ) -> str:
        return (
            f"The predictor evaluated rolling load and thermal trends and classified the primary risk as "
            f"{failure_type}. Mean CPU is {features.cpu_mean:.1f}%, mean memory is "
            f"{features.memory_mean:.1f}%, max temperature is {features.temperature_max:.1f}C, "
            f"and temperature trend is {features.temp_trend:.2f} per interval. "
            f"This yields risk score {risk_score:.2f} with estimated time to failure of {time_to_failure} minutes."
        )


failure_predictor = FailurePredictor()
