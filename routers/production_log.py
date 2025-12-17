# routes/production_log.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from models.production_log import production_logs
from models.employee import Employee
from models.taches import Task
from database.session import get_session

router = APIRouter(prefix="/production-logs", tags=["Production Logs"])

# -------------------------------
# Liste logs
# GET /production-logs
# -------------------------------
@router.get("/")
def get_logs(session: Session = Depends(get_session)):
    try:
        logs = session.exec(select(production_logs)).all()
        return {"status": 200, "data": logs}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Logs par machine
# GET /production-logs/machine/{machine_id}
# -------------------------------

# -------------------------------
@router.get("/employee/{employee_id}")
def get_logs_by_employee(employee_id: int, session: Session = Depends(get_session)):
    try:
        logs = session.exec(select(production_logs).where(production_logs.employee_id == employee_id)).all()
        return {"status": 200, "data": logs}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Créer log (automatique via RFID/ESP32)
# POST /production-logs
# -------------------------------
from pydantic import BaseModel

class UIDModel(BaseModel):
    uid: str  # code RFID
    machine_id: int
    timestamp: datetime

@router.post("/rfid")
def save_production(payload: UIDModel, session: Session = Depends(get_session)):
    try:
        # Chercher l'employé par code RFID
        employee = session.exec(select(Employee).where(Employee.rfid_code == payload.uid)).first()
        if not employee:
            return {"status": 400, "data": []}

        # Chercher la tâche associée à la machine
        task = session.exec(select(Task).where(Task.machine_utilisee == payload.machine_id)).first()
        if not task:
            return {"status": 400, "data": []}

        # Chercher session en cours pour cet employé et tâche
        log = session.exec(
            select(production_logs)
            .where(production_logs.employee_id == employee.id)
            .where(production_logs.task_id == task.id)
            .where(production_logs.fin_tache == None)
        ).first()

        if log:
            # Fin de session : calcul rendement et mise à jour
            log.fin_tache = payload.timestamp
            duration_sec = (log.fin_tache - log.debut_tache).total_seconds()
            log.pieces_produites = task.pieces_par_tache
            log.sets_produits = task.pieces_par_tache // task.pieces_par_set
            log.rendement_pct = (task.pieces_par_tache / duration_sec) * 100  # simple estimation
            session.add(log)
            session.commit()
            session.refresh(log)
            return {"status": 200, "data": log}
        else:
            # Début d'une nouvelle session
            new_log = production_logs(
                employee_id=employee.id,
                task_id=task.id,
                debut_tache=payload.timestamp,
                fin_tache=None,
                pieces_produites=0,
                sets_produits=0,
                rendement_pct=0
            )
            session.add(new_log)
            session.commit()
            session.refresh(new_log)
            return {"status": 200, "data": new_log}

    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier log
# PUT /production-logs/{log_id}
# -------------------------------
@router.put("/{log_id}")
def update_log(log_id: int, log_data: production_logs, session: Session = Depends(get_session)):
    try:
        log = session.get(production_logs, log_id)
        if not log:
            return {"status": 400, "data": []}

        log.debut_tache = log_data.debut_tache
        log.fin_tache = log_data.fin_tache
        log.pieces_produites = log_data.pieces_produites
        log.sets_produits = log_data.sets_produits
        log.rendement_pct = log_data.rendement_pct
        session.add(log)
        session.commit()
        session.refresh(log)
        return {"status": 200, "data": log}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer log
# DELETE /production-logs/{log_id}
# -------------------------------
@router.delete("/{log_id}")
def delete_log(log_id: int, session: Session = Depends(get_session)):
    try:
        log = session.get(production_logs, log_id)
        if not log:
            return {"status": 400, "data": []}
        session.delete(log)
        session.commit()
        return {"status": 200, "data": {"message": "Log deleted successfully"}}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}
