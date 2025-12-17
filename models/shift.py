from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import time

class Shift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str  # Jour / Midjour / Nuit
    heure_debut: time
    heure_fin: time
