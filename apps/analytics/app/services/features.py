from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from shared.schemas import MetricPointIn


@dataclass
class MetricFeatures:
    cpu_mean: float
    cpu_max: float
    memory_mean: float
    memory_max: float
    temperature_mean: float
    temperature_max: float
    network_in_mean: float
    network_out_mean: float
    cpu_trend: float
    temp_trend: float
    pressure_index: float

    def as_vector(self) -> np.ndarray:
        return np.array(
            [
                self.cpu_mean,
                self.cpu_max,
                self.memory_mean,
                self.memory_max,
                self.temperature_mean,
                self.temperature_max,
                self.network_in_mean,
                self.network_out_mean,
                self.cpu_trend,
                self.temp_trend,
                self.pressure_index,
            ],
            dtype=float,
        )


def _linear_slope(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    x_axis = np.arange(len(values), dtype=float)
    slope, _intercept = np.polyfit(x_axis, values, 1)
    return float(slope)


def extract_metric_features(metrics: list[MetricPointIn]) -> MetricFeatures:
    cpu = np.array([item.cpu_usage for item in metrics], dtype=float)
    memory = np.array([item.memory_usage for item in metrics], dtype=float)
    temperature = np.array([item.temperature_c for item in metrics], dtype=float)
    network_in = np.array([item.network_in_mbps for item in metrics], dtype=float)
    network_out = np.array([item.network_out_mbps for item in metrics], dtype=float)

    pressure_index = float(
        (cpu.mean() * 0.35)
        + (memory.mean() * 0.25)
        + (temperature.mean() * 0.40)
        + max(0.0, temperature.max() - 75) * 0.50
    )

    return MetricFeatures(
        cpu_mean=float(cpu.mean()),
        cpu_max=float(cpu.max()),
        memory_mean=float(memory.mean()),
        memory_max=float(memory.max()),
        temperature_mean=float(temperature.mean()),
        temperature_max=float(temperature.max()),
        network_in_mean=float(network_in.mean()),
        network_out_mean=float(network_out.mean()),
        cpu_trend=_linear_slope(cpu),
        temp_trend=_linear_slope(temperature),
        pressure_index=pressure_index,
    )
