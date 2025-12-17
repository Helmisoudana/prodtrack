# routes/machine_session.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.machine_session import MachineSession
from database.session import get_session

router = APIRouter(prefix="/sessions", tags=["Machine Sessions"])

# -------------------------------
# Sessions actuelles
# GET /sessions
# -------------------------------
@router.get("/")
def get_current_sessions(session: Session = Depends(get_session)):
    try:
        sessions = session.exec(select(MachineSession)).all()
        return {"status": 200, "data": sessions}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Session par employé
# GET /sessions/employee/{employee_id}
# -------------------------------
@router.get("/employee/{employee_id}")
def get_sessions_by_employee(employee_id: int, session: Session = Depends(get_session)):
    try:
        sessions = session.exec(select(MachineSession).where(MachineSession.employee_id == employee_id)).all()
        return {"status": 200, "data": sessions}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Session par machine
# GET /sessions/machine/{machine_id}
# -------------------------------
@router.get("/machine/{machine_id}")
def get_sessions_by_machine(machine_id: int, session: Session = Depends(get_session)):
    try:
        sessions = session.exec(select(MachineSession).where(MachineSession.machine_id == machine_id)).all()
        return {"status": 200, "data": sessions}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Créer session (début tâche)
# POST /sessions
# -------------------------------
@router.post("/")
def create_session(session_data: MachineSession, session: Session = Depends(get_session)):
    try:
        session.add(session_data)
        session.commit()
        session.refresh(session_data)
        return {"status": 200, "data": session_data}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Mettre fin session (fin tâche)
# PUT /sessions/{id}/end
# -------------------------------
@router.put("/{session_id}/end")
def end_session(session_id: int, session_data: MachineSession, session: Session = Depends(get_session)):
    try:
        machine_session = session.get(MachineSession, session_id)
        if not machine_session:
            return {"status": 400, "data": []}
        machine_session.fin_tache = session_data.fin_tache
        machine_session.pieces_produites = session_data.pieces_produites
        machine_session.sets_produits = session_data.sets_produits
        machine_session.rendement_pct = session_data.rendement_pct
        session.add(machine_session)
        session.commit()
        session.refresh(machine_session)
        return {"status": 200, "data": machine_session}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer session
# DELETE /sessions/{session_id}
# -------------------------------
@router.delete("/{session_id}")
def delete_session(session_id: int, session: Session = Depends(get_session)):
    try:
        machine_session = session.get(MachineSession, session_id)
        if not machine_session:
            return {"status": 400, "data": []}
        session.delete(machine_session)
        session.commit()
        return {"status": 200, "data": {"message": "Session deleted successfully"}}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}
