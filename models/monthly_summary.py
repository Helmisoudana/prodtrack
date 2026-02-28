# models/monthly_summary.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MonthlySummary(SQLModel, table=True):
    __tablename__ = "monthly_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    periode: str
    date_generation: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Rendement
    rendement_global_pct: Optional[float] = None
    duree_moyenne_taches_min: Optional[float] = None
    taux_anomalie_pct: Optional[float] = None

    # Tâches
    total_taches: Optional[int] = None
    taches_completees: Optional[int] = None
    taches_interrompues: Optional[int] = None
    total_anomalies: Optional[int] = None

    # Employés
    total_employes: Optional[int] = None
    employes_en_travail: Optional[int] = None
    employes_absents: Optional[int] = None
    employes_en_conge: Optional[int] = None

    # Machines
    total_machines: Optional[int] = None
    machines_en_panne: Optional[int] = None

    # Rendement par shift
    rendement_matin: Optional[float] = None
    rendement_jour: Optional[float] = None
    rendement_nuit: Optional[float] = None

    # Fatigue
    score_fatigue_global: Optional[float] = None
    niveau_fatigue_global: Optional[str] = None
    employes_fatigue_critique: Optional[int] = None
    employes_fatigue_eleve: Optional[int] = None
    employes_fatigue_moyen: Optional[int] = None
    employes_fatigue_faible: Optional[int] = None