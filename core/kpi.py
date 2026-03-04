from __future__ import annotations

import pandas as pd


def calculate_kpi(requests_df: pd.DataFrame, events_df: pd.DataFrame) -> dict:
    if requests_df.empty:
        return {
            "avg_cycle_hours": 0,
            "approval_hours": 0,
            "supply_hours": 0,
            "sla_overdue_share": 0,
            "top_delays": pd.DataFrame(columns=["delay_reason", "count"]),
            "queue_by_role": pd.DataFrame(columns=["role", "queue"]),
        }

    closed = requests_df[requests_df["closed_at"].notna()].copy()
    if not closed.empty:
        closed["cycle_h"] = (
            pd.to_datetime(closed["closed_at"]) - pd.to_datetime(closed["created_at"])
        ).dt.total_seconds() / 3600
        avg_cycle = closed["cycle_h"].mean()
    else:
        avg_cycle = 0

    ev = events_df.copy()
    ev["event_ts"] = pd.to_datetime(ev["event_ts"])

    approval = ev[ev["to_status"].isin(["На согласовании", "Согласовано", "Возврат на доработку"])]
    approval_hours = 0 if approval.empty else (approval["event_ts"].max() - approval["event_ts"].min()).total_seconds() / 3600

    supply = ev[ev["to_status"].isin(["В закупке", "В поставке", "На складе"])]
    supply_hours = 0 if supply.empty else (supply["event_ts"].max() - supply["event_ts"].min()).total_seconds() / 3600

    sla_share = ev["sla_breach"].mean() * 100 if "sla_breach" in ev and not ev.empty else 0

    delays = (
        ev[ev["delay_reason"].notna()]
        .groupby("delay_reason", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
        .head(5)
    )

    queue = (
        ev[ev["to_status"].isin(["На согласовании", "В закупке", "В поставке", "На складе"])]
        .groupby("actor_role", as_index=False)
        .size()
        .rename(columns={"actor_role": "role", "size": "queue"})
        .sort_values("queue", ascending=False)
    )

    return {
        "avg_cycle_hours": float(avg_cycle),
        "approval_hours": float(approval_hours),
        "supply_hours": float(supply_hours),
        "sla_overdue_share": float(sla_share),
        "top_delays": delays,
        "queue_by_role": queue,
    }
