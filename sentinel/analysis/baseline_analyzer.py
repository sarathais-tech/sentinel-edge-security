def calculate_deviation(current, average):
    if average <= 0:
        return 0

    return ((current - average) / average) * 100


def analyze_with_baseline(metrics, baseline):
    if baseline["samples"] < 30:
        return {
        "risk_score": 0,
        "status": "APRENDENDO",
        "reasons": [
            f"Baseline em treinamento: {baseline['samples']}/30 amostras"
        ],
        "deviations": {
            "cpu": 0,
            "memory": 0,
            "connections": 0,
        },
    }

    risk_score = 0
    reasons = []

    

    cpu_deviation = calculate_deviation(
        metrics["cpu_percent"],
        baseline["avg_cpu"],
    )

    memory_deviation = calculate_deviation(
        metrics["memory_percent"],
        baseline["avg_memory"],
    )

    connections_deviation = calculate_deviation(
        metrics["active_connections"],
        baseline["avg_connections"],
    )

    if cpu_deviation > 100:
        risk_score += 25
        reasons.append(
            f"CPU {cpu_deviation:.1f}% acima do baseline"
        )

    if memory_deviation > 25:
        risk_score += 25
        reasons.append(
            f"RAM {memory_deviation:.1f}% acima do baseline"
        )

    if connections_deviation > 50:
        risk_score += 30
        reasons.append(
            f"Conexões {connections_deviation:.1f}% acima do baseline"
        )

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
        "reasons": reasons,
        "deviations": {
            "cpu": round(cpu_deviation, 2),
            "memory": round(memory_deviation, 2),
            "connections": round(connections_deviation, 2),
        },
    }