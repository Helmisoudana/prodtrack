from sqlmodel import Field , SQLModel
from typing import Optional
import datetime
class production_logs(SQLModel , table=True):
    id : Optional[int]=Field(default= None , primary_key=True)
    employe_id : Optional[int]=Field(foreign_key="emplyees.id")
    tache_id:Optional[int]=Field(foreign_key="taches.id")
    debut_tache :datetime.datetime
    fin_tache:datetime.datetime
    pieces_produites: int
    sets_produits : int
    rendement_pct : float