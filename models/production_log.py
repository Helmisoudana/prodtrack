from sqlmodel import SQLModel, Field
from typing import Optional

class FactoryLog(SQLModel, table=True):
    __tablename__ = "factory_logs"

    log_id: str = Field(primary_key=True)
    employee_id: Optional[str] = None
    machine_id: Optional[str] = None
    task_name: Optional[str] = None
    tag_event_start: Optional[str] = None
    tag_event_end: Optional[str] = None
    task_duration_min: Optional[float] = None
    shift: Optional[str] = None
    product: Optional[str] = None
    task_status: Optional[str] = None
    anomaly_flag: Optional[int] = None