# models/alert.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    log_id: str
    employee_id: Optional[str] = None
    machine_id: Optional[str] = None
    task_name: Optional[str] = None
    shift: Optional[str] = None
    date_detection: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Prédiction
    is_anomaly: int = 0
    confidence: Optional[float] = None
    score_raw: Optional[float] = None
    label: Optional[str] = None

    # Contexte
    task_duration_min: Optional[float] = None
    task_status: Optional[str] = None
    anomaly_flag_original: Optional[int] = None  # flag original de la DB

    # Statut alerte
    statut: Optional[str] = "Nouvelle"   # Nouvelle | Vue | Traitee