from pydantic import BaseModel
from typing import Optional , List

class uidmodel(BaseModel):
    uid : str
    idtache :int