from __future__ import annotations

import json

import streamlit as st

from core.repo import Repo


def render_process_builder(repo: Repo) -> None:
    st.subheader("Конструктор процесса (low-code)")
    cfg = repo.get_process_config()

    st.markdown("#### Статусы")
    statuses_text = st.text_area("По одному статусу на строку", value="\n".join(cfg["statuses"]), height=200)

    st.markdown("#### Разрешенные переходы (JSON)")
    transitions_text = st.text_area("Формат: {""Черновик"": [""На согласовании""]}", value=json.dumps(cfg["transitions"], ensure_ascii=False, indent=2), height=240)

    st.markdown("#### Правила приоритизации")
    c1, c2 = st.columns(2)
    w_crit = c1.slider("Вес критичности", 0.0, 1.0, float(cfg["priority_weights"]["criticality"]), 0.05)
    w_urg = c2.slider("Вес срочности", 0.0, 1.0, float(cfg["priority_weights"]["urgency"]), 0.05)

    st.markdown("#### SLA по критичности (часы)")
    sla = cfg["sla_by_criticality"]
    cols = st.columns(5)
    new_sla = {}
    for i, k in enumerate(["1", "2", "3", "4", "5"]):
        new_sla[k] = cols[i].number_input(f"Критичность {k}", min_value=1, value=int(sla.get(k, 24)))

    st.markdown("#### Маршруты согласования")
    normal = st.text_input("Normal route (через запятую)", value=", ".join(cfg["approval_routes"]["normal"]))
    emergency = st.text_input("Emergency route (через запятую)", value=", ".join(cfg["approval_routes"]["emergency"]))

    if st.button("Сохранить конфигурацию", type="primary"):
        try:
            transitions = json.loads(transitions_text)
            new_cfg = {
                "statuses": [s.strip() for s in statuses_text.splitlines() if s.strip()],
                "transitions": transitions,
                "priority_weights": {"criticality": w_crit, "urgency": w_urg},
                "sla_by_criticality": {k: int(v) for k, v in new_sla.items()},
                "approval_routes": {
                    "normal": [x.strip() for x in normal.split(",") if x.strip()],
                    "emergency": [x.strip() for x in emergency.split(",") if x.strip()],
                },
            }
            repo.save_process_config(new_cfg)
            st.success("Конфиг сохранен")
        except Exception as exc:
            st.error(f"Ошибка сохранения: {exc}")
