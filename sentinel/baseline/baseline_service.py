import sqlite3
from pathlib import Path


DB_PATH = Path("data/sentinel.db")


def calculate_baseline(hostname):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            AVG(cpu_percent),
            AVG(memory_percent),
            AVG(active_connections),
            COUNT(*)
        FROM metrics
        WHERE hostname = ?
        """,
        (hostname,),
    )

    result = cursor.fetchone()
    conn.close()

    avg_cpu, avg_memory, avg_connections, samples = result

    return {
        "hostname": hostname,
        "avg_cpu": round(avg_cpu or 0, 2),
        "avg_memory": round(avg_memory or 0, 2),
        "avg_connections": round(avg_connections or 0, 2),
        "samples": samples,
    }