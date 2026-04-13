from fastapi import FastAPI

from .services.agent_pipeline import run_agent_pipeline
from shared.schemas import MonitoringAgentInput, OrchestrationResult

app = FastAPI(title="Elio Orchestrator", version="0.1.0")


@app.post("/orchestrate", response_model=OrchestrationResult)
async def orchestrate(payload: MonitoringAgentInput) -> OrchestrationResult:
    return run_agent_pipeline(payload)
