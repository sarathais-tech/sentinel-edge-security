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

    conn.commit()
    conn.close()