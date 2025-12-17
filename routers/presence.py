# routes/presence.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.presence import Presence
from database.session import get_session

router = APIRouter(prefix="/presences", tags=["Presences"])

# -------------------------------
# Liste présences
# GET /presences
# -------------------------------
@router.get("/")
def get_presences(session: Session = Depends(get_session)):
    try:
        presences = session.exec(select(Presence)).all()
        return {"status": 200, "data": presences}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Détail présence
# GET /presences/{presence_id}
# -------------------------------
@router.get("/{presence_id}")
def get_presence(presence_id: int, session: Session = Depends(get_session)):
    try:
        presence = session.get(Presence, presence_id)
        if not presence:
            return {"status": 400, "data": []}
        return {"status": 200, "data": presence}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Ajouter présence
# POST /presences
# -------------------------------
@router.post("/")
def create_presence(presence: Presence, session: Session = Depends(get_session)):
    try:
        session.add(presence)
        session.commit()
        session.refresh(presence)
        return {"status": 200, "data": presence}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier présence
# PUT /presences/{presence_id}
# -------------------------------
@router.put("/{presence_id}")
def update_presence(presence_id: int, presence_data: Presence, session: Session = Depends(get_session)):
    try:
        presence = session.get(Presence, presence_id)
        if not presence:
            return {"status": 400, "data": []}
        presence.employee_id = presence_data.employee_id
        presence.shift_id = presence_data.shift_id
        presence.date = presence_data.date
        presence.heure_debut = presence_data.heure_debut
        presence.heure_fin = presence_data.heure_fin
        session.add(presence)
        session.commit()
        session.refresh(presence)
        return {"status": 200, "data": presence}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer présence
# DELETE /presences/{presence_id}
# -------------------------------
@router.delete("/{presence_id}")
def delete_presence(presence_id: int, session: Session = Depends(get_session)):
    try:
        presence = session.get(Presence, presence_id)
        if not presence:
            return {"status": 400, "data": []}
        session.delete(presence)
        session.commit()
        return {"status": 200, "data": {"message": "Presence deleted successfully"}}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}
