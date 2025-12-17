from sqlmodel import Field , SQLModel
from typing import Optional
class Task(SQLModel , table =True):
    id : Optional[int]=Field(default= None , primary_key=True)
    nom_tache : str
    temps_tache_sec : int
    pieces_par_tache : int
    pieces_par_set : int
    temps_finir_set : int
    machine_utilisee : str
    difficulte : str
    