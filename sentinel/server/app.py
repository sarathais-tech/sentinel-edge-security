from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from sentinel.storage.database import (
    create_tables,
    save_metrics,
    get_latest_metrics,
    get_recent_metrics,
    get_hosts,
    save_event,
    get_last_event,
    get_recent_events,
)

from sentinel.baseline.baseline_service import calculate_baseline
from sentinel.analysis.baseline_analyzer import analyze_with_baseline

app = FastAPI(
    title="Sentinel Server",
    version="0.1.0",
)

create_tables()


class MetricsPayload(BaseModel):
    hostname: str
    cpu_percent: float
    memory_percent: float
    bytes_sent: int
    bytes_received: int
    active_connections: int


def calculate_connection_status(last_seen_string):
    last_seen = datetime.fromisoformat(last_seen_string)

    seconds_since_last_seen = (datetime.now() - last_seen).total_seconds()

    if seconds_since_last_seen <= 120:
        return "ONLINE"

    return "OFFLINE"


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
    return {"status": "ok"}


@app.post("/api/v1/metrics")
def receive_metrics(metrics: MetricsPayload):
    data = metrics.model_dump()

    save_metrics(data)

    baseline = calculate_baseline(metrics.hostname)

    analysis = analyze_with_baseline(
        data,
        baseline,
    )

    last_event = get_last_event(metrics.hostname)

    if last_event is None or last_event["event_type"] == "OFFLINE":
        save_event(
            metrics.hostname,
            "ONLINE",
            "Host enviou telemetria e está online",
        )

    current_status = analysis["status"]
    risk_score = analysis["risk_score"]
    reasons = analysis["reasons"]

    last_event = get_last_event(metrics.hostname)

    if risk_score >= 60:
        if last_event is None or last_event["event_type"] != "RISK_HIGH":
            save_event(
                metrics.hostname,
                "RISK_HIGH",
                f"Risk Score atingiu {risk_score}%",
            )

    elif current_status in [
        "ATENÇÃO",
        "SUSPEITO",
        "CRÍTICO",
    ]:
        if last_event is None or last_event["event_type"] not in [
            "ANOMALY_DETECTED",
            "RISK_HIGH",
        ]:
            message = (
                "; ".join(reasons)
                if reasons
                else "Comportamento fora do baseline detectado"
            )

            save_event(
                metrics.hostname,
                "ANOMALY_DETECTED",
                message,
            )

    elif current_status == "NORMAL":
        if last_event is not None and last_event["event_type"] in [
            "ANOMALY_DETECTED",
            "RISK_HIGH",
        ]:
            save_event(
                metrics.hostname,
                "RISK_NORMALIZED",
                "Host voltou ao comportamento normal",
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
        return {"error": "Host não encontrado"}

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
        "deviations": analysis["deviations"],
    }


@app.get("/api/v1/host/{hostname}")
def get_host_details(hostname: str):
    latest = get_latest_metrics(hostname)

    if latest is None:
        return {"error": "Host não encontrado"}

    baseline = calculate_baseline(hostname)

    analysis = analyze_with_baseline(
        latest,
        baseline,
    )

    hosts = get_hosts()

    host_info = next(
        (host for host in hosts if host["hostname"] == hostname),
        None,
    )

    connection_status = "UNKNOWN"
    last_seen = None
    samples = baseline["samples"]

    if host_info is not None:
        connection_status = calculate_connection_status(host_info["last_seen"])

        last_seen = host_info["last_seen"]
        samples = host_info["samples"]

    all_events = get_recent_events(100)

    host_events = [event for event in all_events if event["hostname"] == hostname][:20]

    return {
        "hostname": hostname,
        "connection_status": connection_status,
        "security_status": analysis["status"],
        "risk_score": analysis["risk_score"],
        "last_seen": last_seen,
        "samples": samples,
        "metrics": {
            "cpu": latest["cpu_percent"],
            "memory": latest["memory_percent"],
            "connections": latest["active_connections"],
            "bytes_sent": latest["bytes_sent"],
            "bytes_received": latest["bytes_received"],
        },
        "baseline": {
            "avg_cpu": baseline["avg_cpu"],
            "avg_memory": baseline["avg_memory"],
            "avg_connections": baseline["avg_connections"],
            "samples": baseline["samples"],
        },
        "deviations": analysis["deviations"],
        "reasons": analysis["reasons"],
        "events": host_events,
    }


@app.get("/api/v1/history/{hostname}")
def get_history(
    hostname: str,
    limit: int = 30,
):
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
        latest = get_latest_metrics(host["hostname"])

        if latest is None:
            continue

        baseline = calculate_baseline(host["hostname"])

        analysis = analyze_with_baseline(
            latest,
            baseline,
        )

        connection_status = calculate_connection_status(host["last_seen"])

        last_event = get_last_event(host["hostname"])

        if connection_status == "OFFLINE":
            if last_event is None or last_event["event_type"] != "OFFLINE":
                save_event(
                    host["hostname"],
                    "OFFLINE",
                    "Host parou de enviar telemetria",
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
                "connections": latest["active_connections"],
            }
        )

    return {"hosts": result}


@app.get("/api/v1/events")
def list_events(
    limit: int = 50,
):
    return {"events": get_recent_events(limit)}


@app.get("/dashboard")
def dashboard_page():
    return FileResponse("sentinel/ui/dashboard.html")


@app.get("/host/{hostname}")
def host_page(hostname: str):
    return FileResponse("sentinel/ui/host.html")
