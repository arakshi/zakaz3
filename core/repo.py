from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from core.db import get_connection
from core.process_config import DEFAULT_CONFIG, dumps_config, loads_config


class Repo:
    def list_equipment(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM equipment ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def list_nomenclature(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM nomenclature ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def count_requests(self) -> int:
        with get_connection() as conn:
            return conn.execute("SELECT COUNT(*) c FROM requests").fetchone()["c"]

    def create_request(self, payload: dict[str, Any], items: list[dict[str, Any]]) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO requests (initiator,equipment_id,reason,priority,needed_by,comments,status,emergency,created_at,scenario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["initiator"],
                    payload["equipment_id"],
                    payload["reason"],
                    payload["priority"],
                    payload["needed_by"],
                    payload.get("comments", ""),
                    payload["status"],
                    int(payload.get("emergency", False)),
                    payload["created_at"],
                    payload.get("scenario", "TO-BE"),
                ),
            )
            request_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO request_items (request_id, nomenclature_id, quantity) VALUES (?, ?, ?)",
                [(request_id, i["nomenclature_id"], i["quantity"]) for i in items],
            )
            conn.execute(
                "INSERT INTO event_log (request_id,event_ts,from_status,to_status,actor_role,reason) VALUES (?, ?, ?, ?, ?, ?)",
                (request_id, payload["created_at"], None, payload["status"], payload.get("actor_role", "Система"), "Создание"),
            )
            conn.commit()
            return int(request_id)

    def list_requests(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        where = ["1=1"]
        params: list[Any] = []
        if filters.get("status"):
            where.append("r.status = ?")
            params.append(filters["status"])
        if filters.get("equipment_id"):
            where.append("r.equipment_id = ?")
            params.append(filters["equipment_id"])
        if filters.get("priority"):
            where.append("r.priority = ?")
            params.append(filters["priority"])
        if filters.get("scenario"):
            where.append("r.scenario = ?")
            params.append(filters["scenario"])

        query = f"""
            SELECT r.*, e.name AS equipment_name, e.site, e.criticality,
                   CAST((julianday(COALESCE(r.closed_at, datetime('now'))) - julianday(r.created_at)) * 24 AS INTEGER) AS cycle_hours
            FROM requests r
            JOIN equipment e ON e.id = r.equipment_id
            WHERE {' AND '.join(where)}
            ORDER BY r.created_at DESC
        """
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_request_details(self, request_id: int) -> dict[str, Any]:
        with get_connection() as conn:
            req = conn.execute(
                "SELECT r.*, e.name as equipment_name, e.site FROM requests r JOIN equipment e ON e.id=r.equipment_id WHERE r.id=?",
                (request_id,),
            ).fetchone()
            if not req:
                raise ValueError("Заявка не найдена")
            items = conn.execute(
                """
                SELECT ri.*, n.name as nomenclature_name, n.unit
                FROM request_items ri
                JOIN nomenclature n ON n.id = ri.nomenclature_id
                WHERE ri.request_id = ?
                """,
                (request_id,),
            ).fetchall()
            approvals = conn.execute("SELECT * FROM approvals WHERE request_id=? ORDER BY decided_at", (request_id,)).fetchall()
            orders = conn.execute("SELECT * FROM orders_supplier WHERE request_id=? ORDER BY created_at", (request_id,)).fetchall()
            events = conn.execute("SELECT * FROM event_log WHERE request_id=? ORDER BY event_ts", (request_id,)).fetchall()
        return {
            "request": dict(req),
            "items": [dict(i) for i in items],
            "approvals": [dict(a) for a in approvals],
            "orders": [dict(o) for o in orders],
            "events": [dict(e) for e in events],
        }

    def update_request_status(self, request_id: int, to_status: str, actor_role: str, reason: str = "") -> None:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        with get_connection() as conn:
            row = conn.execute("SELECT status, created_at, equipment_id FROM requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise ValueError("Заявка не найдена")
            from_status = row["status"]
            eq = conn.execute("SELECT sla_downtime_hours FROM equipment WHERE id=?", (row["equipment_id"],)).fetchone()
            cycle_hours = conn.execute(
                "SELECT (julianday(?) - julianday(?))*24 AS h", (now, row["created_at"])
            ).fetchone()["h"]
            sla_breach = int(cycle_hours > eq["sla_downtime_hours"])
            closed_at = now if to_status in {"Закрыто", "Отказ"} else None
            conn.execute("UPDATE requests SET status=?, closed_at=COALESCE(?, closed_at) WHERE id=?", (to_status, closed_at, request_id))
            conn.execute(
                "INSERT INTO event_log (request_id,event_ts,from_status,to_status,actor_role,reason,sla_breach,delay_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (request_id, now, from_status, to_status, actor_role, reason, sla_breach, reason if sla_breach else None),
            )
            conn.commit()

    def add_approval(self, request_id: int, stage: str, role: str, decision: str, comment: str = "") -> None:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO approvals (request_id,stage,role,decision,comment,decided_at) VALUES (?, ?, ?, ?, ?, ?)",
                (request_id, stage, role, decision, comment, now),
            )
            conn.commit()

    def create_order_for_request(self, request_id: int, supplier: str, markup: float = 1.0) -> int:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        with get_connection() as conn:
            items = conn.execute(
                """
                SELECT ri.nomenclature_id, ri.quantity, n.lead_time_days
                FROM request_items ri
                JOIN nomenclature n ON n.id = ri.nomenclature_id
                WHERE ri.request_id=?
                """,
                (request_id,),
            ).fetchall()
            if not items:
                raise ValueError("Нет позиций для заказа")
            total = sum((i["quantity"] * 1000 * markup) for i in items)
            max_lead = max(i["lead_time_days"] for i in items)
            eta = conn.execute("SELECT date(?, '+' || ? || ' day')", (now, max_lead)).fetchone()[0]
            order_id = conn.execute(
                "INSERT INTO orders_supplier (request_id,supplier,total_price,eta_date,status,created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (request_id, supplier, round(total, 2), eta, "Создан", now),
            ).lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO order_items (order_id,nomenclature_id,quantity,price) VALUES (?, ?, ?, ?)",
                    (order_id, item["nomenclature_id"], item["quantity"], round(1000 * markup, 2)),
                )
            conn.commit()
            return int(order_id)

    def add_delivery(self, order_id: int, partial_ratio: float, received: bool) -> None:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        status = "Принято" if received else "В пути"
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO deliveries (order_id,shipped_at,received_at,partial_ratio,status) VALUES (?, ?, ?, ?, ?)",
                (order_id, now, now if received else None, partial_ratio, status),
            )
            conn.execute("UPDATE orders_supplier SET status=? WHERE id=?", ("Получено" if received else "Отгружено", order_id))
            conn.commit()

    def add_stock_move(self, request_id: int, nomenclature_id: int, move_type: str, qty: float, comment: str = "") -> None:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO stock_moves (request_id,nomenclature_id,move_type,quantity,move_date,comment) VALUES (?, ?, ?, ?, ?, ?)",
                (request_id, nomenclature_id, move_type, qty, now, comment),
            )
            conn.commit()

    def get_process_config(self) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute("SELECT config_json FROM process_config WHERE id=1").fetchone()
            if not row:
                return DEFAULT_CONFIG
            return loads_config(row["config_json"])

    def save_process_config(self, config: dict[str, Any]) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE process_config SET config_json=?, updated_at=datetime('now') WHERE id=1",
                (dumps_config(config),),
            )
            conn.commit()

    def export_requests_df_sql(self) -> str:
        return "SELECT * FROM requests ORDER BY created_at DESC"
