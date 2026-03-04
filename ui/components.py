from __future__ import annotations

import streamlit as st


STATUS_CLASS = {
    "Закрыто": "ok",
    "Отказ": "warn",
    "Возврат на доработку": "warn",
    "На согласовании": "wip",
    "В закупке": "wip",
    "В поставке": "wip",
    "На складе": "wip",
    "Выдано в ТОиР": "wip",
    "Черновик": "wip",
    "Согласовано": "ok",
}


def status_badge(status: str) -> None:
    cls = STATUS_CLASS.get(status, "wip")
    st.markdown(f"<span class='badge badge-{cls}'>{status}</span>", unsafe_allow_html=True)


def metric_card(title: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"<div class='card'><div class='small-muted'>{title}</div><h3 style='margin:6px 0'>{value}</h3><div class='small-muted'>{help_text}</div></div>",
        unsafe_allow_html=True,
    )
