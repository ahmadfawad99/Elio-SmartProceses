from contextlib import asynccontextmanager
import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import actions, anomalies, health, ingestion, machines, predictions, demo
from .simulator import simulator
from .ws_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only start background simulation if NOT on Vercel
    # Vercel doesn't support persistent background tasks in serverless functions
    if not os.environ.get("VERCEL"):
        async def simulation_loop():
            while True:
                readings = simulator.generate_all_readings()
                await manager.broadcast({
                    "type": "metrics_update",
                    "data": readings
                })
                await asyncio.sleep(2)
                
        loop_task = asyncio.create_task(simulation_loop())
        yield
        loop_task.cancel()
    else:
        yield

app = FastAPI(title="Elio API Gateway", version="0.1.0", lifespan=lifespan)

@app.get("/")
async def root_health():
    return {"status": "ok", "service": "elio-api-gateway"}

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

@app.get("/{path:path}")
async def catch_all(path: str):
    return {
        "message": "Path not found by any router",
        "requested_path": path,
        "available_routes": [r.path for r in app.routes]
    }
