import psutil
import socket 
from sentinel.analysis.basic_analyzer import analyze_metrics
from sentinel.storage.database import create_tables, save_metrics
from sentinel.baseline.baseline_service import calculate_baseline



def collect_system_metrics():
    hostname = socket.gethostname()

    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    network = psutil.net_io_counters()
    connections = psutil.net_connections(kind="inet")

    return {
        "hostname": hostname,
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "bytes_sent": network.bytes_sent,
        "bytes_received": network.bytes_recv,
        "active_connections": len(connections),
    }


if __name__ == "__main__":
    data = collect_system_metrics()

    create_tables()
    save_metrics(data)

    baseline = calculate_baseline(data["hostname"])

    print("\nSENTINEL V0.1")
    print("------------------------")
    print(f"Host: {data['hostname']}")
    print(f"CPU: {data['cpu_percent']}%")
    print(f"RAM: {data['memory_percent']}%")
    print(f"Bytes enviados: {data['bytes_sent']}")
    print(f"Bytes recebidos: {data['bytes_received']}")
    print(f"Conexões: {data['active_connections']}")

    analysis = analyze_metrics(data)

print("\nANÁLISE")
print("------------------------")
print(f"Status: {analysis['status']}")
print(f"Risk Score: {analysis['risk_score']}%")

if analysis["reasons"]:
    print("Motivos:")
    for reason in analysis["reasons"]:
        print(f"- {reason}")
else:
    print("Nenhuma anomalia básica detectada.")

print("\nBASELINE")
print("------------------------")
print(f"Amostras: {baseline['samples']}")
print(f"CPU média: {baseline['avg_cpu']}%")
print(f"RAM média: {baseline['avg_memory']}%")
print(f"Conexões médias: {baseline['avg_connections']}")