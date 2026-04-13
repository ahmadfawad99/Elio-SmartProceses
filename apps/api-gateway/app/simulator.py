"""
Sensor simulator for the Elio POC demo.
Generates realistic DC sensor readings for 8 racks and supports
fault injection for the live demo.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone


RACKS = ["A-09", "A-10", "A-11", "A-12", "A-13", "A-14", "B-07", "B-08"]

# Baseline normal operating values per rack
RACK_BASELINES: dict[str, dict] = {
    "A-09": {"cpu_usage": 54, "cpu_temp": 68, "power_kw": 9.2,  "fan_rpm": 3400, "ups_load": 61},
    "A-10": {"cpu_usage": 61, "cpu_temp": 71, "power_kw": 10.1, "fan_rpm": 3300, "ups_load": 65},
    "A-11": {"cpu_usage": 64, "cpu_temp": 72, "power_kw": 10.8, "fan_rpm": 3250, "ups_load": 67},
    "A-12": {"cpu_usage": 58, "cpu_temp": 70, "power_kw": 9.8,  "fan_rpm": 3500, "ups_load": 63},
    "A-13": {"cpu_usage": 57, "cpu_temp": 69, "power_kw": 9.5,  "fan_rpm": 3450, "ups_load": 62},
    "A-14": {"cpu_usage": 46, "cpu_temp": 65, "power_kw": 8.4,  "fan_rpm": 3600, "ups_load": 58},
    "B-07": {"cpu_usage": 72, "cpu_temp": 74, "power_kw": 11.5, "fan_rpm": 3100, "ups_load": 74},
    "B-08": {"cpu_usage": 68, "cpu_temp": 73, "power_kw": 11.0, "fan_rpm": 3200, "ups_load": 70},
}

FAULT_TYPES = ["temp_spike", "fan_failure", "power_anomaly"]


class SensorSimulator:
    def __init__(self) -> None:
        self._faults: dict[str, dict] = {}
        self._history: dict[str, list[dict]] = {rack: [] for rack in RACK_BASELINES}
        self._tick: int = 0

    def inject_fault(self, rack_id: str, fault_type: str) -> None:
        """Inject a fault into a specific rack for the next N ticks."""
        if rack_id not in RACK_BASELINES:
            raise ValueError(f"Unknown rack: {rack_id}")
        if fault_type not in FAULT_TYPES:
            raise ValueError(f"Unknown fault type: {fault_type}")
        self._faults[rack_id] = {"type": fault_type, "ticks_remaining": 15}

    def clear_faults(self) -> None:
        self._faults.clear()

    def get_active_faults(self) -> dict[str, str]:
        return {rack: info["type"] for rack, info in self._faults.items()}

    def generate_reading(self, rack_id: str) -> dict:
        baseline = RACK_BASELINES[rack_id]
        fault = self._faults.get(rack_id)

        # Normal Gaussian noise around baseline
        cpu_usage = baseline["cpu_usage"] + random.gauss(0, 2.5)
        cpu_temp  = baseline["cpu_temp"]  + random.gauss(0, 1.2)
        power_kw  = baseline["power_kw"]  + random.gauss(0, 0.35)
        fan_rpm   = baseline["fan_rpm"]   + random.gauss(0, 60)
        ups_load  = baseline["ups_load"]  + random.gauss(0, 1.8)

        is_anomaly = False
        fault_type: str | None = None

        if fault:
            ft = fault["type"]
            fault_type = ft
            # Build-up intensity over first 5 ticks, then sustain
            ticks_gone = 15 - fault["ticks_remaining"]
            intensity = min(1.0, ticks_gone / 5)

            if ft == "temp_spike":
                cpu_temp  += 26 * intensity + random.gauss(0, 1.5)
                cpu_usage += 38 * intensity + random.gauss(0, 3)
                power_kw  += 6  * intensity + random.gauss(0, 0.3)
                fan_rpm   -= 900 * intensity + random.gauss(0, 60)
                is_anomaly = True

            elif ft == "fan_failure":
                fan_rpm -= 1900 * intensity + random.gauss(0, 40)
                cpu_temp += 20 * intensity + random.gauss(0, 1.5)
                is_anomaly = True

            elif ft == "power_anomaly":
                ups_load += 27 * intensity + random.gauss(0, 2)
                power_kw += 7  * intensity + random.gauss(0, 0.4)
                is_anomaly = True

            fault["ticks_remaining"] -= 1
            if fault["ticks_remaining"] <= 0:
                del self._faults[rack_id]

        reading = {
            "rack_id":    rack_id,
            "cpu_usage":  round(max(0.0,  min(100.0, cpu_usage)), 1),
            "cpu_temp":   round(max(20.0, min(105.0, cpu_temp)), 1),
            "power_kw":   round(max(0.0,  power_kw), 2),
            "fan_rpm":    round(max(0.0,  fan_rpm)),
            "ups_load":   round(max(0.0,  min(100.0, ups_load)), 1),
            "is_anomaly": is_anomaly,
            "fault_type": fault_type,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }

        # Keep rolling history (last 30 readings per rack)
        hist = self._history[rack_id]
        hist.append(reading)
        if len(hist) > 30:
            hist.pop(0)

        return reading

    def generate_all_readings(self) -> list[dict]:
        self._tick += 1
        return [self.generate_reading(rack_id) for rack_id in RACK_BASELINES]

    def get_history(self, rack_id: str) -> list[dict]:
        return list(self._history.get(rack_id, []))

    def get_all_history(self) -> dict[str, list[dict]]:
        return {rack: list(readings) for rack, readings in self._history.items()}

    def get_snapshot(self) -> list[dict]:
        """Return the latest reading for each rack."""
        result = []
        for rack_id, history in self._history.items():
            if history:
                result.append(history[-1])
        return result


simulator = SensorSimulator()
