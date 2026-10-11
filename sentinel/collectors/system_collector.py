import psutil
import socket
import time

from sentinel.agent.client import send_metrics


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
    print("\nSENTINEL AGENT")
    print("------------------------")
    print("Monitoramento iniciado.")
    print("Intervalo: 60 segundos")
    print("Pressione Ctrl+C para encerrar.\n")

    try:
        while True:
            data = collect_system_metrics()

            print("------------------------")
            print(f"Host: {data['hostname']}")
            print(f"CPU: {data['cpu_percent']}%")
            print(f"RAM: {data['memory_percent']}%")
            print(f"Conexões: {data['active_connections']}")

            server_result = send_metrics(data)

            if server_result["success"]:
                response = server_result["response"]
                analysis = response["analysis"]
                baseline = response["baseline"]

                print(f"Status: {analysis['status']}")
                print(f"Risk Score: {analysis['risk_score']}%")
                print(f"Baseline: {baseline['samples']} amostras")

                if analysis["reasons"]:
                    print("Motivos:")
                    for reason in analysis["reasons"]:
                        print(f"- {reason}")
            else:
                print("Falha ao enviar métricas.")
                print(server_result["error"])

            print("\nPróxima coleta em 60 segundos...\n")
            time.sleep(60)

    except KeyboardInterrupt:
        print("\nSentinel Agent encerrado.")