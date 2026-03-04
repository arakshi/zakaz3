from __future__ import annotations

import random
from datetime import datetime, timedelta

from core.db import get_connection


DELAY_REASONS_ASIS = [
    "Ручное согласование",
    "Ожидание КП",
    "Логистика",
    "Нет резерва на складе",
    "Согласование бюджета",
]

DELAY_REASONS_TOBE = [
    "Уточнение спецификации",
    "Транспортное окно",
    "Частичная поставка",
]


def seed_if_empty() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) c FROM requests").fetchone()["c"]
        if count > 0:
            return

        equipment = [
            ("Турбина Т-110", "Цех 1", 5, 12),
            ("Насос НЦ-45", "Цех 2", 4, 24),
            ("Конвейер К-3", "Склад", 3, 48),
            ("Компрессор КМ-12", "Компрессорная", 5, 10),
            ("Печь П-7", "Термоучасток", 4, 18),
        ]
        conn.executemany(
            "INSERT INTO equipment (name,site,criticality,sla_downtime_hours) VALUES (?, ?, ?, ?)",
            equipment,
        )

        nomenclature = [
            ("Подшипник 6205", "шт", 12, 7),
            ("Ремень клиновой A-1200", "шт", 10, 5),
            ("Фильтр масляный F-10", "шт", 20, 3),
            ("Датчик вибрации VIB-2", "шт", 5, 14),
            ("Клапан обратный КО-50", "шт", 4, 9),
            ("Смазка индустриальная", "кг", 50, 2),
            ("Кабель силовой 3х4", "м", 100, 4),
            ("Прокладка термостойкая", "шт", 30, 6),
            ("Сальник вала", "шт", 15, 8),
            ("Блок питания 24В", "шт", 6, 12),
        ]
        conn.executemany(
            "INSERT INTO nomenclature (name,unit,min_stock,lead_time_days) VALUES (?, ?, ?, ?)",
            nomenclature,
        )

        statuses = [
            "Черновик",
            "На согласовании",
            "Согласовано",
            "В закупке",
            "В поставке",
            "На складе",
            "Выдано в ТОиР",
            "Закрыто",
        ]
        roles = ["Заявитель ТОиР", "Планировщик ТОиР", "Снабжение", "Склад", "Руководитель"]
        reasons = ["Плановое ТО", "Аварийный ремонт", "Вибрация", "Протечка", "Износ"]

        req_count = random.randint(240, 340)
        equipment_ids = [r["id"] for r in conn.execute("SELECT id FROM equipment").fetchall()]
        nomenclature_ids = [r["id"] for r in conn.execute("SELECT id FROM nomenclature").fetchall()]

        for _ in range(req_count):
            scenario = random.choice(["AS-IS", "TO-BE"])
            equipment_id = random.choice(equipment_ids)
            criticality = conn.execute(
                "SELECT criticality FROM equipment WHERE id=?", (equipment_id,)
            ).fetchone()["criticality"]
            created = datetime.utcnow() - timedelta(days=random.randint(1, 120), hours=random.randint(0, 23))

            # Делает различие сценариев заметным: AS-IS значительно дольше
            if scenario == "AS-IS":
                base_delay = random.randint(90, 260)
            else:
                base_delay = random.randint(18, 110)

            is_closed = random.random() > 0.08
            current_status = "Закрыто" if is_closed else random.choice(statuses[:-1])
            closed = created + timedelta(hours=base_delay) if is_closed else None
            needed = created + timedelta(days=1 if criticality >= 4 else 5)

            cur = conn.execute(
                """
                INSERT INTO requests (initiator,equipment_id,reason,priority,needed_by,comments,status,emergency,created_at,closed_at,scenario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"Инициатор {random.randint(1, 20)}",
                    equipment_id,
                    random.choice(reasons),
                    random.randint(1, 5),
                    needed.date().isoformat(),
                    "Сгенерировано автоматически",
                    current_status,
                    int(random.random() < 0.15),
                    created.isoformat(sep=" ", timespec="seconds"),
                    closed.isoformat(sep=" ", timespec="seconds") if closed else None,
                    scenario,
                ),
            )
            req_id = cur.lastrowid

            for _ in range(random.randint(1, 4)):
                conn.execute(
                    "INSERT INTO request_items (request_id,nomenclature_id,quantity) VALUES (?, ?, ?)",
                    (req_id, random.choice(nomenclature_ids), random.randint(1, 12)),
                )

            chain = statuses[: statuses.index(current_status) + 1] if current_status in statuses else ["Черновик"]
            ts = created
            for idx, st in enumerate(chain):
                if scenario == "AS-IS":
                    delta = random.randint(20, 76)
                    breach = int(delta > 34)
                    delay_reason = random.choice(DELAY_REASONS_ASIS) if random.random() < 0.78 else None
                else:
                    delta = random.randint(6, 22)
                    breach = int(delta > 18 and random.random() < 0.45)
                    # Даже в TO-BE могут быть редкие причины задержек
                    delay_reason = random.choice(DELAY_REASONS_TOBE) if random.random() < 0.28 else None

                ts += timedelta(hours=delta)
                conn.execute(
                    """
                    INSERT INTO event_log (request_id,event_ts,from_status,to_status,actor_role,reason,sla_breach,delay_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req_id,
                        ts.isoformat(sep=" ", timespec="seconds"),
                        chain[idx - 1] if idx > 0 else None,
                        st,
                        random.choice(roles),
                        "Автогенерация",
                        breach,
                        delay_reason,
                    ),
                )

            if current_status in {"В закупке", "В поставке", "На складе", "Выдано в ТОиР", "Закрыто"}:
                order = conn.execute(
                    "INSERT INTO orders_supplier (request_id,supplier,total_price,eta_date,status,created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        req_id,
                        random.choice(["ООО ПромСнаб", "АО Ресурс", "ТехМаркет"]),
                        random.randint(15_000, 450_000),
                        (created + timedelta(days=random.randint(3, 25))).date().isoformat(),
                        "Получено" if current_status in {"На складе", "Выдано в ТОиР", "Закрыто"} else "Отгружено",
                        created.isoformat(sep=" ", timespec="seconds"),
                    ),
                ).lastrowid
                conn.execute(
                    "INSERT INTO deliveries (order_id,shipped_at,received_at,partial_ratio,status) VALUES (?, ?, ?, ?, ?)",
                    (
                        order,
                        (created + timedelta(days=2)).isoformat(sep=" ", timespec="seconds"),
                        (created + timedelta(days=5)).isoformat(sep=" ", timespec="seconds") if current_status in {"На складе", "Выдано в ТОиР", "Закрыто"} else None,
                        random.choice([0.4, 0.7, 1.0]),
                        "Принято" if current_status in {"На складе", "Выдано в ТОиР", "Закрыто"} else "В пути",
                    ),
                )

            if current_status in {"На складе", "Выдано в ТОиР", "Закрыто"}:
                nm = random.choice(nomenclature_ids)
                conn.execute(
                    "INSERT INTO stock_moves (request_id,nomenclature_id,move_type,quantity,move_date,comment) VALUES (?, ?, ?, ?, ?, ?)",
                    (req_id, nm, "приход", random.randint(1, 10), created.isoformat(sep=" ", timespec="seconds"), "Демо"),
                )
                if current_status in {"Выдано в ТОиР", "Закрыто"}:
                    conn.execute(
                        "INSERT INTO stock_moves (request_id,nomenclature_id,move_type,quantity,move_date,comment) VALUES (?, ?, ?, ?, ?, ?)",
                        (req_id, nm, "выдача", random.randint(1, 8), (created + timedelta(days=1)).isoformat(sep=" ", timespec="seconds"), "Демо"),
                    )

        conn.commit()
