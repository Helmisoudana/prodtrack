# routers/production_log.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
import uuid

from models.production_log import FactoryLog
from database.session import get_session
from ml.alert_service import check_and_save_alert

router = APIRouter(prefix="/production-logs", tags=["Production Logs"])

# GET /production-logs
@router.get("")
def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        offset = (page - 1) * limit
        total  = len(session.exec(select(FactoryLog)).all())
        logs   = session.exec(select(FactoryLog).offset(offset).limit(limit)).all()
        return {
            "status": 200,
            "data": logs,
            "pagination": {
                "page": page, "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /production-logs/{log_id}
@router.get("/{log_id}")
def get_log(log_id: str, session: Session = Depends(get_session)):
    try:
        log = session.get(FactoryLog, log_id)
        if not log:
            return {"status": 404, "data": []}
        return {"status": 200, "data": log}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /production-logs/employee/{employee_id}
@router.get("/employee/{employee_id}")
def get_logs_by_employee(
    employee_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        offset = (page - 1) * limit
        total  = len(session.exec(select(FactoryLog).where(FactoryLog.employee_id == employee_id)).all())
        logs   = session.exec(
            select(FactoryLog).where(FactoryLog.employee_id == employee_id)
            .offset(offset).limit(limit)
        ).all()
        return {
            "status": 200, "data": logs,
            "pagination": {"page": page, "limit": limit, "total": total,
                           "pages": (total + limit - 1) // limit}
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /production-logs/machine/{machine_id}
@router.get("/machine/{machine_id}")
def get_logs_by_machine(
    machine_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        offset = (page - 1) * limit
        total  = len(session.exec(select(FactoryLog).where(FactoryLog.machine_id == machine_id)).all())
        logs   = session.exec(
            select(FactoryLog).where(FactoryLog.machine_id == machine_id)
            .offset(offset).limit(limit)
        ).all()
        return {
            "status": 200, "data": logs,
            "pagination": {"page": page, "limit": limit, "total": total,
                           "pages": (total + limit - 1) // limit}
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# ── POST /production-logs ─────────────────────────────────────────────
# Crée le log ET vérifie l'anomalie automatiquement
@router.post("")
def create_log(log: FactoryLog, session: Session = Depends(get_session)):
    try:
        if not log.log_id:
            log.log_id = str(uuid.uuid4())

        session.add(log)
        session.commit()
        session.refresh(log)

        # ── Détection anomalie automatique ──────────────────────────
        alert_result = check_and_save_alert(log, session)

        return {
            "status": 200,
            "data": log,
            "alert": alert_result
        }
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# PUT /production-logs/{log_id}
@router.put("/{log_id}")
def update_log(log_id: str, log_data: FactoryLog, session: Session = Depends(get_session)):
    try:
        log = session.get(FactoryLog, log_id)
        if not log:
            return {"status": 404, "data": []}

        update_data = log_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(log, key, value)

        session.add(log)
        session.commit()
        session.refresh(log)
        return {"status": 200, "data": log}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# DELETE /production-logs/{log_id}
@router.delete("/{log_id}")
def delete_log(log_id: str, session: Session = Depends(get_session)):
    try:
        log = session.get(FactoryLog, log_id)
        if not log:
            return {"status": 404, "data": []}
        session.delete(log)
        session.commit()
        return {"status": 200, "data": {"message": "Log deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}