from fastapi import FastAPI
from pydantic import BaseModel
from sentinel.storage.database import create_tables, save_metrics

app = FastAPI(
    title="Sentinel Server",
    version="0.1.0",
)

class MetricsPayload(BaseModel):
    hostname: str
    cpu_percent: float
    memory_percent: float
    bytes_sent: int
    bytes_received: int
    active_connections: int

@app.get("/")
def root():
    return {
        "project": "Sentinel",
        "service": "Sentinel Server",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.post("/api/v1/metrics")
def receive_metrics(metrics: MetricsPayload):
    create_tables()

    data = metrics.model_dump()
    save_metrics(data)

    return {
        "received": True,
        "hostname": metrics.hostname,
        "message": "Métricas recebidas e salvas com sucesso"
    }