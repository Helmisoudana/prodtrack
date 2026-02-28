# routes/machine.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from models.machine import Machine
from database.session import get_session

router = APIRouter(prefix="/machines", tags=["Machines"])

# GET /machines?page=1&limit=20
@router.get("")
def get_machines(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        offset = (page - 1) * limit
        total = len(session.exec(select(Machine)).all())
        machines = session.exec(select(Machine).offset(offset).limit(limit)).all()
        return {
            "status": 200,
            "data": machines,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /machines/{id}
@router.get("/{machine_id}")
def get_machine(machine_id: str, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            return {"status": 400, "data": []}
        return {"status": 200, "data": machine}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# POST /machines
@router.post("")
def create_machine(machine: Machine, session: Session = Depends(get_session)):
    try:
        session.add(machine)
        session.commit()
        session.refresh(machine)
        return {"status": 200, "data": machine}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# PUT /machines/{id}
@router.put("/{machine_id}")
def update_machine(machine_id: str, machine_data: Machine, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            return {"status": 400, "data": []}

        update_data = machine_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(machine, key, value)

        session.add(machine)
        session.commit()
        session.refresh(machine)
        return {"status": 200, "data": machine}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# DELETE /machines/{id}
@router.delete("/{machine_id}")
def delete_machine(machine_id: str, session: Session = Depends(get_session)):
    try:
        machine = session.get(Machine, machine_id)
        if not machine:
            return {"status": 400, "data": []}
        session.delete(machine)
        session.commit()
        return {"status": 200, "data": {"message": "Machine deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# GET /machines/{id}/logs
@router.get("/{machine_id}/logs")
def get_machine_logs(
    machine_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        from models.production_log import FactoryLog
        offset = (page - 1) * limit
        all_logs = session.exec(select(FactoryLog).where(FactoryLog.machine_id == machine_id)).all()
        total = len(all_logs)
        logs = session.exec(
            select(FactoryLog)
            .where(FactoryLog.machine_id == machine_id)
            .offset(offset)
            .limit(limit)
        ).all()
        return {
            "status": 200,
            "data": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}