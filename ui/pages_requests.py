from __future__ import annotations

import pandas as pd
import streamlit as st

from core.repo import Repo
from core.services import RequestService
from ui.components import status_badge


ROLES = ["Заявитель ТОиР", "Планировщик ТОиР", "Снабжение", "Склад", "Руководитель", "Админ"]


def render_requests_page(repo: Repo, service: RequestService) -> None:
    st.subheader("Заявки: управление сквозным потоком")

    with st.expander("➕ Создать новую заявку", expanded=False):
        equipments = repo.list_equipment()
        nomenclature = repo.list_nomenclature()
        cfg = repo.get_process_config()

        c1, c2, c3 = st.columns(3)
        initiator = c1.text_input("Инициатор", value="Инженер ТОиР")
        eq = c2.selectbox("Оборудование", equipments, format_func=lambda x: f"{x['name']} ({x['site']})")
        emergency = c3.checkbox("Аварийная ветка", value=False)

        reason = st.text_input("Причина", value="Плановое обслуживание")
        needed_by = st.date_input("Нужно к", value=service.default_needed_by(eq["criticality"], emergency))
        priority = service.calculate_priority(eq["criticality"], needed_by, cfg)
        st.info(f"Автоприоритет по правилам: **{priority}**")

        pick_items = st.multiselect("Позиции", nomenclature, format_func=lambda x: x["name"])
        items = []
        for item in pick_items:
            qty = st.number_input(f"Кол-во: {item['name']}", min_value=1.0, value=1.0, step=1.0, key=f"qty_{item['id']}")
            items.append({"nomenclature_id": item["id"], "quantity": qty})

        comments = st.text_area("Комментарии")
        if st.button("Создать заявку", type="primary"):
            if not items:
                st.warning("Добавьте хотя бы одну позицию.")
            else:
                request_id = repo.create_request(
                    {
                        "initiator": initiator,
                        "equipment_id": eq["id"],
                        "reason": reason,
                        "priority": priority,
                        "needed_by": needed_by.isoformat(),
                        "comments": comments,
                        "status": "На согласовании" if not emergency else "Согласовано",
                        "emergency": emergency,
                        "actor_role": st.session_state.role,
                        "created_at": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                    items,
                )
                st.success(f"Заявка №{request_id} создана")

    st.markdown("### Реестр")
    c1, c2, c3, c4 = st.columns(4)
    statuses = [""] + repo.get_process_config()["statuses"]
    eqs = [None] + repo.list_equipment()
    filters = {
        "status": c1.selectbox("Статус", statuses, format_func=lambda x: x or "Все"),
        "equipment_id": c2.selectbox("Оборудование", eqs, format_func=lambda x: "Все" if not x else x["name"]),
        "priority": c3.selectbox("Приоритет", [None, 1, 2, 3, 4, 5], format_func=lambda x: "Все" if not x else str(x)),
        "scenario": c4.selectbox("Сценарий", [None, "AS-IS", "TO-BE"], format_func=lambda x: x or "Оба"),
    }
    if filters["equipment_id"]:
        filters["equipment_id"] = filters["equipment_id"]["id"]

    df = pd.DataFrame(repo.list_requests(filters))
    if df.empty:
        st.info("Нет заявок по фильтрам")
        return

    st.download_button("Экспорт CSV", df.to_csv(index=False).encode("utf-8-sig"), file_name="requests_export.csv")

    for _, row in df.head(60).iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.markdown(f"**#{row['id']} {row['reason']}**  ")
            c1.caption(f"{row['equipment_name']} · {row['site']} · Инициатор: {row['initiator']}")
            with c2:
                status_badge(row["status"])
            c3.metric("Приоритет", row["priority"])
            c4.metric("Цикл, ч", row["cycle_hours"])

            with st.expander("Быстрые действия"):
                details = repo.get_request_details(int(row["id"]))
                st.dataframe(pd.DataFrame(details["items"])[["nomenclature_name", "quantity", "unit"]], use_container_width=True)
                allowed = service.allowed_transitions(row["status"])
                next_status = st.selectbox(
                    f"Новый статус для #{row['id']}",
                    [None] + allowed,
                    key=f"status_{row['id']}",
                    format_func=lambda x: x or "--",
                )
                reason = st.text_input("Комментарий", key=f"comment_{row['id']}")
                col_a, col_b, col_c = st.columns(3)
                if col_a.button("Сохранить статус", key=f"save_{row['id']}") and next_status:
                    service.change_status(int(row["id"]), next_status, st.session_state.role, reason)
                    st.success("Статус обновлен")
                if col_b.button("Согласовать", key=f"approve_{row['id']}"):
                    service.register_approval(int(row["id"]), st.session_state.role, "Согласовано", reason)
                    st.success("Решение зафиксировано")
                if col_c.button("Вернуть на доработку", key=f"rework_{row['id']}"):
                    service.register_approval(int(row["id"]), st.session_state.role, "Доработка", reason)
                    st.warning("Возврат на доработку")

                if st.button("Создать заказ поставщику", key=f"order_{row['id']}"):
                    oid = repo.create_order_for_request(int(row["id"]), "ООО ПромСнаб", 1.15)
                    st.success(f"Создан заказ #{oid}")
                order_id = st.number_input("ID заказа", min_value=1, value=1, key=f"oid_{row['id']}")
                part = st.slider("Частичный приход", 0.1, 1.0, 1.0, 0.1, key=f"part_{row['id']}")
                if st.button("Зафиксировать поставку", key=f"delivery_{row['id']}"):
                    repo.add_delivery(int(order_id), float(part), received=part >= 1.0)
                    st.success("Поставка добавлена")

                html = service.printable_card_html(details)
                st.download_button(
                    "Печать карточки (HTML)",
                    data=html.encode("utf-8"),
                    file_name=f"request_{row['id']}.html",
                    mime="text/html",
                    key=f"print_{row['id']}",
                )
