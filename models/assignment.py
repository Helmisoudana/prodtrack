from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class Assignment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    machine_id: int = Field(foreign_key="machine.id")
    task_id: int = Field(foreign_key="task.id")
    date_affectation: date
    shift_id: int = Field(foreign_key="shift.id")
    source: str  # IA / Manuel
    score_ia: Optional[float] = None
