from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.db import get_connection
from core.kpi import calculate_kpi
from ui.components import metric_card


def render_dashboard_page(scenario: str) -> None:
    st.subheader("KPI дашборд сквозного процесса")
    with get_connection() as conn:
        req_df = pd.read_sql_query("SELECT * FROM requests WHERE scenario=?", conn, params=(scenario,))
        ev_df = pd.read_sql_query(
            "SELECT e.* FROM event_log e JOIN requests r ON r.id=e.request_id WHERE r.scenario=?", conn, params=(scenario,)
        )
        req_cmp = pd.read_sql_query("SELECT scenario, created_at, closed_at FROM requests", conn)
        ev_cmp = pd.read_sql_query(
            "SELECT r.scenario, e.delay_reason FROM event_log e JOIN requests r ON r.id=e.request_id", conn
        )

    kpi = calculate_kpi(req_df, ev_df)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Среднее время цикла", f"{kpi['avg_cycle_hours']:.1f} ч", "Создание → Закрытие")
    with c2:
        metric_card("Время согласования", f"{kpi['approval_hours']:.1f} ч")
    with c3:
        metric_card("Закупка + доставка", f"{kpi['supply_hours']:.1f} ч")
    with c4:
        metric_card("Доля SLA-просрочек", f"{kpi['sla_overdue_share']:.1f}%")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Топ причин задержек")
        if not kpi["top_delays"].empty:
            fig = px.bar(kpi["top_delays"], x="delay_reason", y="count", color="count", color_continuous_scale="Blues", template="plotly_white")
            fig.update_layout(font_color="#0f172a", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            st.plotly_chart(fig, use_container_width=True)
        else:
            # fallback: показываем, что в целом по сценарию встречалось
            fallback = (
                ev_df[ev_df["delay_reason"].notna()]
                .groupby("delay_reason", as_index=False)
                .size()
                .rename(columns={"size": "count"})
                .sort_values("count", ascending=False)
                .head(5)
            )
            if not fallback.empty:
                fig = px.bar(fallback, x="delay_reason", y="count", color="count", color_continuous_scale="Blues", template="plotly_white")
                fig.update_layout(font_color="#0f172a", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Для выбранного сценария задержек не зафиксировано")

    with col2:
        st.markdown("#### Очередь по ролям")
        if not kpi["queue_by_role"].empty:
            fig = px.pie(kpi["queue_by_role"], names="role", values="queue", hole=0.45, template="plotly_white")
            fig.update_layout(font_color="#0f172a", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных")

    st.markdown("#### Сравнение AS-IS vs TO-BE")
    if not req_cmp.empty:
        df = req_cmp.copy()
        df = df[df["closed_at"].notna()]
        df["cycle_h"] = (pd.to_datetime(df["closed_at"]) - pd.to_datetime(df["created_at"])).dt.total_seconds() / 3600
        cmp_df = df.groupby("scenario", as_index=False)["cycle_h"].mean().sort_values("cycle_h", ascending=False)

        if {"AS-IS", "TO-BE"}.issubset(set(cmp_df["scenario"])):
            asis = float(cmp_df[cmp_df["scenario"] == "AS-IS"]["cycle_h"].iloc[0])
            tobe = float(cmp_df[cmp_df["scenario"] == "TO-BE"]["cycle_h"].iloc[0])
            improve = ((asis - tobe) / asis * 100) if asis else 0.0
            m1, m2, m3 = st.columns(3)
            m1.metric("AS-IS, ср. цикл", f"{asis:.1f} ч")
            m2.metric("TO-BE, ср. цикл", f"{tobe:.1f} ч")
            m3.metric("Ускорение TO-BE", f"{improve:.1f}%")

        fig = px.bar(cmp_df, x="scenario", y="cycle_h", color="scenario", text=cmp_df["cycle_h"].round(1), template="plotly_white")
        fig.update_layout(yaxis_title="Средний цикл, ч", font_color="#0f172a", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
        st.plotly_chart(fig, use_container_width=True)

        # сравнение причин задержек по сценариям
        delays_cmp = (
            ev_cmp[ev_cmp["delay_reason"].notna()]
            .groupby(["scenario", "delay_reason"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        if not delays_cmp.empty:
            st.markdown("#### Причины задержек: AS-IS vs TO-BE")
            fig_delay = px.bar(
                delays_cmp,
                x="delay_reason",
                y="count",
                color="scenario",
                barmode="group",
            )
            fig_delay.update_layout(font_color="#0f172a", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            st.plotly_chart(fig_delay, use_container_width=True)
