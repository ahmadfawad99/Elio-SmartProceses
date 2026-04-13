from enum import Enum


class MachineStatus(str, Enum):
    healthy = "healthy"
    warning = "warning"
    critical = "critical"
    offline = "offline"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ActionMode(str, Enum):
    manual = "manual"
    auto = "auto"


class ActionType(str, Enum):
    load_balance = "load_balance"
    cooling_adjustment = "cooling_adjustment"
    alert = "alert"
    restart_service = "restart_service"


class ActionStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    executed = "executed"
    failed = "failed"
    simulated = "simulated"


class AgentName(str, Enum):
    monitoring = "monitoring"
    prediction = "prediction"
    decision = "decision"
    action = "action"
