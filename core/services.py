from __future__ import annotations

from datetime import date, datetime, timedelta

from core.repo import Repo


class RequestService:
    def __init__(self, repo: Repo):
        self.repo = repo

    def calculate_priority(self, criticality: int, needed_by: date, config: dict) -> int:
        days_left = max((needed_by - date.today()).days, 0)
        urgency = 5 if days_left <= 2 else 4 if days_left <= 5 else 3 if days_left <= 10 else 2
        w_crit = config["priority_weights"]["criticality"]
        w_urg = config["priority_weights"]["urgency"]
        score = round(criticality * w_crit + urgency * w_urg)
        return max(1, min(5, score))

    def default_needed_by(self, criticality: int, emergency: bool) -> date:
        if emergency:
            return date.today() + timedelta(days=1)
        gap = {5: 2, 4: 4, 3: 7, 2: 10, 1: 14}
        return date.today() + timedelta(days=gap.get(criticality, 7))

    def allowed_transitions(self, current_status: str) -> list[str]:
        config = self.repo.get_process_config()
        return config["transitions"].get(current_status, [])

    def change_status(self, request_id: int, to_status: str, actor_role: str, reason: str = "") -> None:
        self.repo.update_request_status(request_id, to_status, actor_role, reason)

    def register_approval(self, request_id: int, role: str, decision: str, comment: str = "") -> None:
        stage = f"Этап {role}"
        self.repo.add_approval(request_id, stage, role, decision, comment)
        mapping = {
            "Согласовано": "Согласовано",
            "Отклонено": "Отказ",
            "Доработка": "Возврат на доработку",
        }
        self.repo.update_request_status(request_id, mapping[decision], role, comment)

    def printable_card_html(self, details: dict) -> str:
        req = details["request"]
        rows = "".join(
            f"<tr><td>{i['nomenclature_name']}</td><td>{i['quantity']}</td><td>{i['unit']}</td></tr>" for i in details["items"]
        )
        return f"""
        <html><head><meta charset='utf-8'></head>
        <body style='font-family:Arial;padding:24px'>
            <h2>Карточка заявки №{req['id']}</h2>
            <p><b>Статус:</b> {req['status']} | <b>Инициатор:</b> {req['initiator']}</p>
            <p><b>Оборудование:</b> {req['equipment_name']} ({req['site']})</p>
            <p><b>Причина:</b> {req['reason']}</p>
            <table border='1' cellpadding='8' cellspacing='0'>
              <tr><th>Номенклатура</th><th>Количество</th><th>Ед.</th></tr>
              {rows}
            </table>
            <p>Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </body></html>
        """
