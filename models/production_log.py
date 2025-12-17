from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

class production_logs(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employe_id: int = Field(foreign_key="employee.id")
    tache_id:Optional[int]=Field(foreign_key="task.id")
    debut_tache :datetime.datetime
    fin_tache:datetime.datetime
    pieces_produites: int
    sets_produits : int
    rendement_pct : float
