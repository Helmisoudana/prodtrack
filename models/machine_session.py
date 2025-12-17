from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MachineSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    machine_id: int = Field(foreign_key="machine.id")
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    shift_id: int = Field(foreign_key="shift.id")
    
    debut_session: datetime  # premier tag (avant tâche)
    fin_session: Optional[datetime] = None  # dernier tag (après tâche)
    
    duree_sec: Optional[int] = None
    pieces: int = 0
    sets: int = 0
    rendement_calcule: Optional[float] = None
