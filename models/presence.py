from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Presence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    shift_id: int = Field(foreign_key="shift.id")
    check_in: datetime
    check_out: Optional[datetime] = None
    statut: str = "present"  # present / absent / retard
