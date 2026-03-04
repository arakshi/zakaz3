from __future__ import annotations

import sqlite3
from pathlib import Path

from core.process_config import DEFAULT_CONFIG, dumps_config

DB_PATH = Path("data/app.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                site TEXT NOT NULL,
                criticality INTEGER NOT NULL,
                sla_downtime_hours INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS nomenclature (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                min_stock REAL NOT NULL,
                lead_time_days INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                initiator TEXT NOT NULL,
                equipment_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                priority INTEGER NOT NULL,
                needed_by TEXT NOT NULL,
                comments TEXT,
                status TEXT NOT NULL,
                emergency INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                closed_at TEXT,
                scenario TEXT NOT NULL DEFAULT 'TO-BE',
                FOREIGN KEY(equipment_id) REFERENCES equipment(id)
            );

            CREATE TABLE IF NOT EXISTS request_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                nomenclature_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE,
                FOREIGN KEY(nomenclature_id) REFERENCES nomenclature(id)
            );

            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                role TEXT NOT NULL,
                decision TEXT NOT NULL,
                comment TEXT,
                decided_at TEXT NOT NULL,
                FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders_supplier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                supplier TEXT NOT NULL,
                total_price REAL NOT NULL,
                eta_date TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(request_id) REFERENCES requests(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                nomenclature_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders_supplier(id) ON DELETE CASCADE,
                FOREIGN KEY(nomenclature_id) REFERENCES nomenclature(id)
            );

            CREATE TABLE IF NOT EXISTS deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                shipped_at TEXT NOT NULL,
                received_at TEXT,
                partial_ratio REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders_supplier(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS stock_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                nomenclature_id INTEGER NOT NULL,
                move_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                move_date TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY(request_id) REFERENCES requests(id),
                FOREIGN KEY(nomenclature_id) REFERENCES nomenclature(id)
            );

            CREATE TABLE IF NOT EXISTS event_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                event_ts TEXT NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                actor_role TEXT,
                reason TEXT,
                sla_breach INTEGER NOT NULL DEFAULT 0,
                delay_reason TEXT,
                FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS process_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        exists = conn.execute("SELECT COUNT(*) AS c FROM process_config").fetchone()["c"]
        if exists == 0:
            conn.execute(
                "INSERT INTO process_config (id, config_json, updated_at) VALUES (1, ?, datetime('now'))",
                (dumps_config(DEFAULT_CONFIG),),
            )
        conn.commit()
