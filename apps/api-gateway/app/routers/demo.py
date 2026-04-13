from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from ..ws_manager import manager
from ..simulator import simulator
from ..agents.pipeline import run_pipeline
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "readings": simulator.get_snapshot(),
                "history": simulator.get_all_history(),
                "active_faults": simulator.get_active_faults()
            }
        })
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.post("/simulate-fault")
async def simulate_fault(rack_id: str, fault_type: str, background_tasks: BackgroundTasks):
    simulator.inject_fault(rack_id, fault_type)
    
    # Run the agent pipeline in the background when a fault is injected
    # We wait a few seconds for the simulator loop to pick up the fault
    async def trigger_pipeline():
        await asyncio.sleep(2)
        readings = simulator.get_history(rack_id)
        await run_pipeline(rack_id, readings, manager.broadcast)

    background_tasks.add_task(trigger_pipeline)
    
    return {"status": "fault_injected", "rack_id": rack_id, "fault_type": fault_type}

@router.post("/clear-faults")
async def clear_faults():
    simulator.clear_faults()
    return {"status": "faults_cleared"}

@router.get("/telemetry")
async def get_telemetry():
    # In serverless mode, we generate a new reading on each poll
    # to maintain the "live" feel
    readings = simulator.generate_all_readings()
    return {
        "readings": readings,
        "history": simulator.get_all_history(),
        "active_faults": simulator.get_active_faults()
    }
