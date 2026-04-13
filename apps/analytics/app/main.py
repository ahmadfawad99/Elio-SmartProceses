from fastapi import FastAPI

from shared.schemas import AnomalyEvent, MetricPointIn, MetricWindow, PredictionEvent

from .services.anomaly import anomaly_detector
from .services.prediction import failure_predictor

app = FastAPI(title="Elio Analytics", version="0.1.0")


@app.post("/detect/anomaly", response_model=AnomalyEvent)
async def detect_anomaly(metric: MetricPointIn) -> AnomalyEvent:
    return anomaly_detector.detect([metric])


@app.post("/detect/anomaly/window", response_model=AnomalyEvent)
async def detect_anomaly_window(payload: MetricWindow) -> AnomalyEvent:
    return anomaly_detector.detect(payload.metrics)


@app.post("/predict/failure", response_model=PredictionEvent)
async def predict_failure(metric: MetricPointIn) -> PredictionEvent:
    return failure_predictor.predict([metric])


@app.post("/predict/failure/window", response_model=PredictionEvent)
async def predict_failure_window(payload: MetricWindow) -> PredictionEvent:
    return failure_predictor.predict(payload.metrics)
