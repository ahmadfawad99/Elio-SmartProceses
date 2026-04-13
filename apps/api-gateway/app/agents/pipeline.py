"""
Self-contained async agent pipeline for the Elio demo.

4-agent sequential chain:
  Monitor  →  Diagnose  →  Action  →  Report

Each step streams a WebSocket event as it executes, creating the
live "reasoning trace" that is the centrepiece of the demo.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Awaitable, Callable
from uuid import uuid4


# ── helpers ──────────────────────────────────────────────────────────────────

Broadcaster = Callable[[dict], Awaitable[None]]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _anomaly_score(reading: dict) -> float:
    cpu_temp  = reading.get("cpu_temp",  70)
    cpu_usage = reading.get("cpu_usage", 50)
    fan_rpm   = reading.get("fan_rpm",   3400)
    ups_load  = reading.get("ups_load",  65)
    power_kw  = reading.get("power_kw",  10)

    score = (
        _clamp((cpu_temp  - 60) / 45, 0, 1) * 0.35
        + (cpu_usage / 100)                  * 0.25
        + _clamp((3500 - fan_rpm) / 3500, 0, 1) * 0.18
        + (ups_load / 100)                   * 0.12
        + _clamp(power_kw / 18, 0, 1)        * 0.10
    )
    return round(_clamp(score, 0.0, 0.99), 3)


def _classify_severity(score: float, reading: dict) -> str:
    cpu_temp = reading.get("cpu_temp", 70)
    if score >= 0.85 or cpu_temp >= 92:
        return "critical"
    if score >= 0.68 or cpu_temp >= 84:
        return "high"
    if score >= 0.48:
        return "medium"
    return "low"


def _failure_type(reading: dict) -> tuple[str, str, str]:
    """Returns (failure_type, root_cause, impact)."""
    cpu_temp  = reading.get("cpu_temp",  70)
    fan_rpm   = reading.get("fan_rpm",   3400)
    ups_load  = reading.get("ups_load",  65)
    cpu_usage = reading.get("cpu_usage", 50)
    rack_id   = reading.get("rack_id",   "unknown")

    if cpu_temp >= 85 and fan_rpm < 2800:
        return (
            "cooling_fan_failure",
            f"CPU temperature {cpu_temp}°C with fan RPM at {fan_rpm:.0f} (expected >3200). "
            f"Primary failure: cooling fan degradation causing thermal accumulation in {rack_id}.",
            "Thermal shutdown risk within 4–6 hours. Adjacent racks may absorb heat spillover.",
        )
    if cpu_temp >= 85:
        return (
            "thermal_overload",
            f"CPU temperature {cpu_temp}°C exceeds safe threshold (80°C). "
            f"High compute utilisation ({cpu_usage}%) driving sustained thermal output "
            f"without adequate cooling response.",
            "Risk of CPU throttling and hardware damage within 2–4 hours.",
        )
    if ups_load >= 88:
        return (
            "power_capacity_breach",
            f"UPS load at {ups_load}% exceeds recommended 85% threshold. "
            f"Power draw {reading.get('power_kw', 0):.1f} kW approaching circuit capacity.",
            "Risk of power interruption. Unplanned shutdown could affect all rack services.",
        )
    if fan_rpm < 2000:
        return (
            "fan_mechanical_failure",
            f"Fan RPM at {fan_rpm:.0f} is critically low (normal: >3000). "
            "Likely mechanical failure or controller fault.",
            "Active cooling loss. Temperature will rise rapidly — critical within 30–60 min.",
        )
    return (
        "resource_degradation",
        f"Multi-metric deviation: cpu_temp={cpu_temp}°C, cpu_usage={cpu_usage}%, "
        f"fan_rpm={fan_rpm:.0f}.",
        "Early warning — escalation likely if workload continues at current pace.",
    )


ENGINEERS = ["Ahmed K.", "Sara M.", "Omar F.", "Lina R.", "Reem A."]


# ── main pipeline ─────────────────────────────────────────────────────────────

async def run_pipeline(
    rack_id: str,
    readings: list[dict],
    broadcast: Broadcaster,
) -> dict:
    """
    Run the 4-agent pipeline, streaming a WebSocket event after each step.

    Returns the generated work-order dict.
    """
    latest = readings[-1] if readings else {}
    correlation_id = str(uuid4())[:8].upper()

    # ── Step 1: Monitor Agent ─────────────────────────────────────────────────
    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Monitor Agent",
            "status":         "running",
            "step":           1,
            "message":        f"Scanning sensor stream for rack {rack_id}…",
            "correlation_id": correlation_id,
        },
    })
    await asyncio.sleep(0.9)

    score    = _anomaly_score(latest)
    severity = _classify_severity(score, latest)

    monitor_reasoning = (
        f"Evaluated rack {rack_id}: "
        f"cpu_temp={latest.get('cpu_temp')}°C, "
        f"cpu_usage={latest.get('cpu_usage')}%, "
        f"fan_rpm={latest.get('fan_rpm'):.0f}, "
        f"power_kw={latest.get('power_kw')}kW, "
        f"ups_load={latest.get('ups_load')}%. "
        f"Anomaly score computed at {score:.2f}. "
        f"Severity classified as {severity.upper()} based on thermal and utilisation thresholds."
    )

    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Monitor Agent",
            "status":         "complete",
            "step":           1,
            "message":        f"Anomaly detected · Score: {score:.2f} · Severity: {severity.upper()}",
            "reasoning":      monitor_reasoning,
            "anomaly_score":  score,
            "severity":       severity,
            "correlation_id": correlation_id,
        },
    })
    await asyncio.sleep(1.1)

    # ── Step 2: Diagnose Agent ────────────────────────────────────────────────
    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Diagnose Agent",
            "status":         "running",
            "step":           2,
            "message":        "Analysing root cause and predicting failure mode…",
            "correlation_id": correlation_id,
        },
    })
    await asyncio.sleep(1.3)

    failure_type, root_cause, impact = _failure_type(latest)
    ttf = max(5, int((1 - score) * 180))

    diagnose_reasoning = (
        f"Root cause: {root_cause} "
        f"| Estimated impact: {impact} "
        f"| Time-to-failure window: ~{ttf} minutes."
    )

    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":                 "Diagnose Agent",
            "status":                "complete",
            "step":                  2,
            "message":               f"Root cause: {failure_type.replace('_', ' ').title()} · TTF: ~{ttf} min",
            "reasoning":             diagnose_reasoning,
            "failure_type":          failure_type,
            "time_to_failure_minutes": ttf,
            "severity":              severity,
            "correlation_id":        correlation_id,
        },
    })
    await asyncio.sleep(0.9)

    # ── Step 3: Action Agent ──────────────────────────────────────────────────
    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Action Agent",
            "status":         "running",
            "step":           3,
            "message":        f"Severity {severity.upper()} — selecting optimal remediation…",
            "correlation_id": correlation_id,
        },
    })
    await asyncio.sleep(1.0)

    engineer = random.choice(ENGINEERS)

    if severity in ("critical", "high"):
        if "thermal" in failure_type or "cooling" in failure_type or "fan" in failure_type:
            action_type = "cooling_adjustment"
        else:
            action_type = "load_balance"
        priority   = "URGENT"
        sla_hours  = 2
    elif severity == "medium":
        action_type = "alert"
        priority    = "HIGH"
        sla_hours   = 4
    else:
        action_type = "alert"
        priority    = "MEDIUM"
        sla_hours   = 8

    wo_id = f"WO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid4())[:4].upper()}"

    action_reasoning = (
        f"Severity {severity.upper()} with failure mode '{failure_type}' requires immediate "
        f"{action_type.replace('_', ' ')}. "
        f"Assigning to {engineer} with {priority} priority and {sla_hours}h SLA. "
        f"Work order {wo_id} auto-generated and logged."
    )

    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Action Agent",
            "status":         "complete",
            "step":           3,
            "message":        f"Work order {wo_id} created · Assigned: {engineer} · SLA: {sla_hours}h",
            "reasoning":      action_reasoning,
            "work_order_id":  wo_id,
            "assigned_to":    engineer,
            "action_type":    action_type,
            "correlation_id": correlation_id,
        },
    })
    await asyncio.sleep(0.8)

    # ── Step 4: Report Agent ──────────────────────────────────────────────────
    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Report Agent",
            "status":         "running",
            "step":           4,
            "message":        "Generating incident report and writing audit trail…",
            "correlation_id": correlation_id,
        },
    })
    await asyncio.sleep(0.8)

    summary = (
        f"Incident {correlation_id} — {failure_type.replace('_', ' ').title()} on {rack_id}. "
        f"Anomaly score {score:.2f} triggered {severity.upper()} alert at "
        f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC. "
        f"{action_type.replace('_', ' ').title()} dispatched. "
        f"{engineer} notified. All agent decisions logged with full reasoning trace."
    )

    await broadcast({
        "type": "agent_event",
        "data": {
            "agent":          "Report Agent",
            "status":         "complete",
            "step":           4,
            "message":        "Incident report generated · Audit trail complete",
            "reasoning":      summary,
            "correlation_id": correlation_id,
        },
    })

    # ── Emit finalised work order ─────────────────────────────────────────────
    work_order = {
        "id":                     wo_id,
        "rack_id":                rack_id,
        "severity":               severity,
        "failure_type":           failure_type,
        "action_type":            action_type,
        "priority":               priority,
        "assigned_to":            engineer,
        "sla_hours":              sla_hours,
        "anomaly_score":          score,
        "time_to_failure_minutes": ttf,
        "reasoning":              diagnose_reasoning,
        "created_at":             datetime.now(timezone.utc).isoformat(),
        "correlation_id":         correlation_id,
    }

    await broadcast({
        "type": "work_order",
        "data": work_order,
    })

    return work_order
