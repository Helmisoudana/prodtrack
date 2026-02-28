from sqlmodel import SQLModel, Field
from typing import Optional

class employee(SQLModel, table=True):
    __tablename__ = "employee"
    
    employee_id: str = Field(primary_key=True)
    nom: Optional[str] = None
    prenom: Optional[str] = None
    sexe: Optional[str] = None
    date_naissance: Optional[str] = None
    age: Optional[int] = None
    etat_civil: Optional[str] = None
    nombre_enfants: Optional[int] = None
    niveau_etude: Optional[str] = None
    poste: Optional[str] = None
    departement: Optional[str] = None
    type_contrat: Optional[str] = None
    anciennete_annees: Optional[int] = None
    salaire_mensuel: Optional[int] = None
    prime_rendement: Optional[int] = None
    heures_travail_semaine: Optional[int] = None
    heures_absence_mois: Optional[int] = None
    retards_mois: Optional[int] = None
    jours_conge_restant: Optional[int] = None
    statut_presence: Optional[str] = None
    rfid_uid: Optional[str] = None
    shift_travail: Optional[str] = None
    performance_moyenne: Optional[float] = None
    taux_rendement: Optional[float] = None
    accidents_travail: Optional[int] = None
    maladies_professionnelles: Optional[int] = None
    evaluation_manager: Optional[int] = None
    risque_absenteisme: Optional[str] = None
    risque_depart: Optional[str] = None
    date_embauche: Optional[str] = None  # ← c'était "Option" sans al fin