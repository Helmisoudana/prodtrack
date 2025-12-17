# routes/machine.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.machine import Machine
from models.machine_session import MachineSession
from models.production_log import production_logs
from database.session import get_session

router = APIRouter(prefix="/machines", tags=["Machines"])

# -------------------------------
# Liste machines
# GET /machines
# -------------------------------
@router.get("/")
def get_machines(session: Session = Depends(get_session)):
    try:
        machines = session.exec(select(Machine)).all()
        return {"status": 200, "data": machines}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Détail machine
# GET /machines/{id}
# -------------------------------
@router.get("/{machine_id}")
def get_machine(machine_id: int, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            return {"status": 400, "data": []}
        return {"status": 200, "data": machine}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Créer machine
# POST /machines
# -------------------------------
@router.post("/")
def create_machine(machine: Machine, session: Session = Depends(get_session)):
    try:
        session.add(machine)
        session.commit()
        session.refresh(machine)
        return {"status": 200, "data": machine}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier machine
# PUT /machines/{id}
# -------------------------------
@router.put("/{machine_id}")
def update_machine(machine_id: int, machine_data: Machine, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            return {"status": 400, "data": []}
        machine.nom_machine = machine_data.nom_machine
        machine.taches = machine_data.taches
        machine.status = machine_data.status
        session.add(machine)
        session.commit()
        session.refresh(machine)
        return {"status": 200, "data": machine}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer machine
# DELETE /machines/{id}
# -------------------------------
@router.delete("/{machine_id}")
def delete_machine(machine_id: int, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            return {"status": 400, "data": []}
        session.delete(machine)
        session.commit()
        return {"status": 200, "data": {"message": "Machine deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Sessions en cours
# GET /machines/{id}/sessions
# -------------------------------
@router.get("/{machine_id}/sessions")
def get_machine_sessions(machine_id: int, session: Session = Depends(get_session)):
    try:
        sessions = session.exec(
            select(MachineSession)
            .where(MachineSession.machine_id == machine_id)
            .where(MachineSession.fin_tache == None)  # sessions actives
        ).all()
        return {"status": 200, "data": sessions}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Rendement historique
# GET /machines/{id}/logs
# -------------------------------
