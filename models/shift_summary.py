# models/shift_summary.py
from sqlmodel import SQLModel, Field
from typing import Optional

class ShiftSummary(SQLModel, table=True):
    __tablename__ = "shift_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str
    shift: str
    date_generation: str

    # Rendement
    rendement_pct: Optional[float] = None
    duree_moyenne_min: Optional[float] = None
    taux_anomalie_pct: Optional[float] = None

    # Tâches
    total_taches: Optional[int] = None
    taches_completees: Optional[int] = None
    taches_interrompues: Optional[int] = None
    total_anomalies: Optional[int] = None

    # Employés
    total_employes_shift: Optional[int] = None

    # Fatigue
    score_fatigue_shift: Optional[float] = None
    niveau_fatigue_shift: Optional[str] = None
    employes_fatigue_critique: Optional[int] = None
    employes_fatigue_eleve: Optional[int] = None
    employes_fatigue_moyen: Optional[int] = None
    employes_fatigue_faible: Optional[int] = None