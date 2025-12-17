from sqlmodel import Field , SQLModel 
from typing import Optional
class Employee(SQLModel , table=True):
    id : Optional[int]=Field(default= None , primary_key=True)
    nom : str
    identifiant_ui : str
    role : str
    actif: bool = True

