from __future__ import annotations

import streamlit as st

from core.db import init_db
from core.demo_data import seed_if_empty
from core.repo import Repo
from core.services import RequestService
from ui.pages_dashboard import render_dashboard_page
from ui.pages_process_builder import render_process_builder
from ui.pages_requests import ROLES, render_requests_page
from ui.styles import BASE_CSS

st.set_page_config(page_title="ТОиР: Заявка-Заказ-Поставка", layout="wide")
st.markdown(BASE_CSS, unsafe_allow_html=True)

init_db()
seed_if_empty()

repo = Repo()
service = RequestService(repo)

if "role" not in st.session_state:
    st.session_state.role = ROLES[0]
if "scenario" not in st.session_state:
    st.session_state.scenario = "TO-BE"

with st.sidebar:
    st.title("ТОиР Control Tower")
    st.session_state.role = st.selectbox("Роль", ROLES, index=ROLES.index(st.session_state.role))
    st.session_state.scenario = st.radio("Сценарий", ["AS-IS", "TO-BE"], index=1 if st.session_state.scenario == "TO-BE" else 0)
    page = st.radio("Раздел", ["Дашборд KPI", "Заявки", "Конструктор процесса"])
    st.caption("Low-code прототип сквозного процесса")

st.title("Оптимизация процесса «Заявка – заказ – поставка»")
st.caption(f"Текущая роль: {st.session_state.role} · Сценарий: {st.session_state.scenario}")

if page == "Дашборд KPI":
    render_dashboard_page(st.session_state.scenario)
elif page == "Заявки":
    render_requests_page(repo, service)
else:
    if st.session_state.role != "Админ":
        st.warning("Экран доступен только роли Админ")
    else:
        render_process_builder(repo)
