from sqlmodel import SQLModel, Field
from typing import Optional

class Machine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str
    type_machine: str
    actif: bool = True
