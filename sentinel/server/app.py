from fastapi import FastAPI
from pydantic import BaseModel

from sentinel.storage.database import create_tables, save_metrics
from sentinel.baseline.baseline_service import calculate_baseline
from sentinel.analysis.baseline_analyzer import analyze_with_baseline


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

    baseline = calculate_baseline(metrics.hostname)

    analysis = analyze_with_baseline(
        data,
        baseline,
    )

    return {
        "received": True,
        "hostname": metrics.hostname,
        "baseline": {
            "samples": baseline["samples"],
            "avg_cpu": baseline["avg_cpu"],
            "avg_memory": baseline["avg_memory"],
            "avg_connections": baseline["avg_connections"],
        },
        "analysis": {
            "status": analysis["status"],
            "risk_score": analysis["risk_score"],
            "reasons": analysis["reasons"],
            "deviations": analysis["deviations"],
        },
    }