# routes/shift.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.shift import Shift
from database.session import get_session

router = APIRouter(prefix="/shifts", tags=["Shifts"])

# -------------------------------
# Liste shifts
# GET /shifts
# -------------------------------
@router.get("/")
def get_shifts(session: Session = Depends(get_session)):
    try:
        shifts = session.exec(select(Shift)).all()
        return {"status": 200, "data": shifts}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Détail shift
# GET /shifts/{shift_id}
# -------------------------------
@router.get("/{shift_id}")
def get_shift(shift_id: int, session: Session = Depends(get_session)):
    try:
        shift = session.get(Shift, shift_id)
        if not shift:
            return {"status": 400, "data": []}
        return {"status": 200, "data": shift}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Créer shift
# POST /shifts
# -------------------------------
@router.post("/")
def create_shift(shift: Shift, session: Session = Depends(get_session)):
    try:
        session.add(shift)
        session.commit()
        session.refresh(shift)
        return {"status": 200, "data": shift}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier shift
# PUT /shifts/{shift_id}
# -------------------------------
@router.put("/{shift_id}")
def update_shift(shift_id: int, shift_data: Shift, session: Session = Depends(get_session)):
    try:
        shift = session.get(Shift, shift_id)
        if not shift:
            return {"status": 400, "data": []}
        shift.nom_shift = shift_data.nom_shift
        shift.heure_debut = shift_data.heure_debut
        shift.heure_fin = shift_data.heure_fin
        session.add(shift)
        session.commit()
        session.refresh(shift)
        return {"status": 200, "data": shift}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer shift
# DELETE /shifts/{shift_id}
# -------------------------------
@router.delete("/{shift_id}")
def delete_shift(shift_id: int, session: Session = Depends(get_session)):
    try:
        shift = session.get(Shift, shift_id)
        if not shift:
            return {"status": 400, "data": []}
        session.delete(shift)
        session.commit()
        return {"status": 200, "data": {"message": "Shift deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}
