from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


RequestStatus = Literal[
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
]


class Equipment(BaseModel):
    id: Optional[int] = None
    name: str = Field(min_length=2)
    site: str
    criticality: int = Field(ge=1, le=5)
    sla_downtime_hours: int = Field(gt=0)


class Nomenclature(BaseModel):
    id: Optional[int] = None
    name: str
    unit: str
    min_stock: float = Field(ge=0)
    lead_time_days: int = Field(ge=0)


class RequestItem(BaseModel):
    nomenclature_id: int
    quantity: float = Field(gt=0)


class MaintenanceRequest(BaseModel):
    id: Optional[int] = None
    initiator: str
    equipment_id: int
    reason: str
    priority: int = Field(ge=1, le=5)
    needed_by: date
    comments: str = ""
    status: RequestStatus
    emergency: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalDecision(BaseModel):
    request_id: int
    stage: str
    role: str
    decision: Literal["Согласовано", "Отклонено", "Доработка"]
    comment: str = ""


class SupplierOrder(BaseModel):
    id: Optional[int] = None
    request_id: int
    supplier: str
    total_price: float = Field(ge=0)
    eta_date: date
    status: str


class Delivery(BaseModel):
    id: Optional[int] = None
    order_id: int
    shipped_at: date
    received_at: Optional[date] = None
    partial_ratio: float = Field(ge=0, le=1)
    status: str
