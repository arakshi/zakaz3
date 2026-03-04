from __future__ import annotations

import json
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "statuses": [
        "Черновик",
        "На согласовании",
        "Согласовано",
        "В закупке",
        "В поставке",
        "На складе",
        "Выдано в ТОиР",
        "Закрыто",
        "Возврат на доработку",
        "Отказ",
    ],
    "transitions": {
        "Черновик": ["На согласовании", "Отказ"],
        "На согласовании": ["Согласовано", "Возврат на доработку", "Отказ"],
        "Возврат на доработку": ["На согласовании", "Отказ"],
        "Согласовано": ["В закупке"],
        "В закупке": ["В поставке"],
        "В поставке": ["На складе"],
        "На складе": ["Выдано в ТОиР"],
        "Выдано в ТОиР": ["Закрыто"],
        "Отказ": [],
        "Закрыто": [],
    },
    "priority_weights": {"criticality": 0.6, "urgency": 0.4},
    "sla_by_criticality": {"1": 240, "2": 120, "3": 72, "4": 36, "5": 12},
    "approval_routes": {
        "normal": ["Планировщик ТОиР", "Руководитель", "Снабжение"],
        "emergency": ["Руководитель"],
    },
}


def dumps_config(config: dict[str, Any]) -> str:
    return json.dumps(config, ensure_ascii=False, indent=2)


def loads_config(raw: str) -> dict[str, Any]:
    return json.loads(raw)
