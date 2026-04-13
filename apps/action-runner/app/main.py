from fastapi import FastAPI

from shared.enums import ActionStatus
from shared.schemas import ActionAgentInput, ActionAgentOutput

app = FastAPI(title="Elio Action Runner", version="0.1.0")


@app.post("/execute", response_model=ActionAgentOutput)
async def execute_action(payload: ActionAgentInput) -> ActionAgentOutput:
    return ActionAgentOutput(
        execution_status=ActionStatus.simulated,
        executed_action=payload.decision_output.recommended_action,
        side_effects=["Simulation only"],
        reasoning="Action executed in simulation mode pending environment integration.",
    )
