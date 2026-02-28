from sqlmodel import SQLModel, Field
from typing import Optional

class Machine(SQLModel, table=True):
    __tablename__ = "machines_realiste_textile"

    machine_id: str = Field(primary_key=True)
    nom_machine: Optional[str] = None
    type_machine: Optional[str] = None
    atelier: Optional[str] = None
    tache: Optional[str] = None
    unite_production: Optional[str] = None
    capacite: Optional[int] = None
    temps_par_unite_min: Optional[float] = None
    temps_total_tache_min: Optional[int] = None
    operateurs_requis: Optional[int] = None
    pannes_mois: Optional[int] = None
    etat_machine: Optional[str] = None
    annee_installation: Optional[int] = None
    marque: Optional[str] = None
    consommation_energie: Optional[str] = None
    rendement_machine: Optional[float] = None