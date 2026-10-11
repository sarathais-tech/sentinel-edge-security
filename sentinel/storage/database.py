import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path("data/sentinel.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            hostname TEXT NOT NULL,
            cpu_percent REAL NOT NULL,
            memory_percent REAL NOT NULL,
            bytes_sent INTEGER NOT NULL,
            bytes_received INTEGER NOT NULL,
            active_connections INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_metrics(metrics):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO metrics (
            timestamp,
            hostname,
            cpu_percent,
            memory_percent,
            bytes_sent,
            bytes_received,
            active_connections
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(),
            metrics["hostname"],
            metrics["cpu_percent"],
            metrics["memory_percent"],
            metrics["bytes_sent"],
            metrics["bytes_received"],
            metrics["active_connections"],
        ),
    )

def get_latest_metrics(hostname):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            hostname,
            cpu_percent,
            memory_percent,
            bytes_sent,
            bytes_received,
            active_connections
        FROM metrics
        WHERE hostname = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (hostname,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "hostname": row[0],
        "cpu_percent": row[1],
        "memory_percent": row[2],
        "bytes_sent": row[3],
        "bytes_received": row[4],
        "active_connections": row[5],
    }
def get_recent_metrics(hostname, limit=30):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            timestamp,
            cpu_percent,
            memory_percent,
            active_connections
        FROM metrics
        WHERE hostname = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (hostname, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    rows.reverse()

    return [
        {
            "timestamp": row[0],
            "cpu_percent": row[1],
            "memory_percent": row[2],
            "active_connections": row[3],
        }
        for row in rows
    ]
def get_hosts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            hostname,
            COUNT(*) as samples,
            MAX(id) as last_id
        FROM metrics
        GROUP BY hostname
        ORDER BY hostname
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "hostname": row[0],
            "samples": row[1],
            "last_id": row[2],
        }
        for row in rows
    ]
    conn.commit()
    conn.close()

    