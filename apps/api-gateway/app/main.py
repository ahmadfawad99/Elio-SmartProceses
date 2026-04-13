from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import actions, anomalies, health, ingestion, machines, predictions, demo
from .simulator import simulator
from .ws_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background sensor simulation
    async def simulation_loop():
        while True:
            readings = simulator.generate_all_readings()
            await manager.broadcast({
                "type": "metrics_update",
                "data": readings
            })
            await asyncio.sleep(2) # Update every 2 seconds
            
    loop_task = asyncio.create_task(simulation_loop())
    yield
    loop_task.cancel()

app = FastAPI(title="Elio API Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(anomalies.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")
app.include_router(machines.router, prefix="/api/v1")
app.include_router(demo.router)
