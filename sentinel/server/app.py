from fastapi import FastAPI
from pydantic import BaseModel
from sentinel.storage.database import (
    create_tables,
    save_metrics,
    get_latest_metrics,
    get_recent_metrics,
    get_hosts,
)
from sentinel.baseline.baseline_service import calculate_baseline
from sentinel.analysis.baseline_analyzer import analyze_with_baseline
from fastapi.responses import FileResponse
from datetime import datetime


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
@app.get("/api/v1/dashboard/{hostname}")
def get_dashboard(hostname: str):
    latest = get_latest_metrics(hostname)

    if latest is None:
        return {
            "error": "Host não encontrado"
        }

    baseline = calculate_baseline(hostname)

    analysis = analyze_with_baseline(
        latest,
        baseline,
    )

    return {
        "hostname": hostname,
        "status": analysis["status"],
        "risk_score": analysis["risk_score"],
        "metrics": {
            "cpu": latest["cpu_percent"],
            "memory": latest["memory_percent"],
            "connections": latest["active_connections"],
        },
        "baseline": {
            "samples": baseline["samples"],
            "avg_cpu": baseline["avg_cpu"],
            "avg_memory": baseline["avg_memory"],
            "avg_connections": baseline["avg_connections"],
        },
        "reasons": analysis["reasons"],
    }

@app.get("/dashboard")
def dashboard_page():
    return FileResponse(
        "sentinel/ui/dashboard.html"
    )

@app.get("/api/v1/history/{hostname}")
def get_history(hostname: str, limit: int = 30):
    return {
        "hostname": hostname,
        "history": get_recent_metrics(
            hostname,
            limit,
        ),
    }

@app.get("/api/v1/hosts")
def list_hosts():
    hosts = get_hosts()

    result = []

    for host in hosts:
        latest = get_latest_metrics(
            host["hostname"]
        )

        baseline = calculate_baseline(
            host["hostname"]
        )

        analysis = analyze_with_baseline(
            latest,
            baseline,
        )

        last_seen = datetime.fromisoformat(
            host["last_seen"]
        )

        seconds_since_last_seen = (
            datetime.now() - last_seen
        ).total_seconds()

        connection_status = (
            "ONLINE"
            if seconds_since_last_seen <= 120
            else "OFFLINE"
        )

        result.append(
            {
                "hostname": host["hostname"],
                "samples": host["samples"],
                "connection_status": connection_status,
                "last_seen": host["last_seen"],
                "status": analysis["status"],
                "risk_score": analysis["risk_score"],
                "cpu": latest["cpu_percent"],
                "memory": latest["memory_percent"],
                "connections": latest[
                    "active_connections"
                ],
            }
        )

    return {
        "hosts": result
    }