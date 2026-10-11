def analyze_metrics(metrics):
    risk_score = 0
    reasons = []

    if metrics["cpu_percent"] > 85:
        risk_score += 25
        reasons.append("CPU muito alta")

    if metrics["memory_percent"] > 90:
        risk_score += 30
        reasons.append("Uso de memória muito alto")

    if metrics["active_connections"] > 150:
        risk_score += 20
        reasons.append("Quantidade elevada de conexões")

    if risk_score == 0:
        status = "NORMAL"
    elif risk_score <= 30:
        status = "ATENÇÃO"
    elif risk_score <= 60:
        status = "SUSPEITO"
    else:
        status = "CRÍTICO"

    return {
        "risk_score": min(risk_score, 100),
        "status": status,
        "reasons": reasons
    }
