from sqlmodel import SQLModel, Field
from typing import Optional

class RFIDTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code_rfid: str
    type: str  # 'employee' ou 'machine'
    employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    machine_id: Optional[int] = Field(default=None, foreign_key="machine.id")
    actif: bool = True
