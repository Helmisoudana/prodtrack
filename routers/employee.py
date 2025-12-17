# routes/employee.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta

from models.employee import Employee
from models.production_log import production_logs
from database.session import get_session

router = APIRouter(prefix="/employees", tags=["Employees"])

# -------------------------------
# Liste employés
# GET /employees
# -------------------------------
@router.get("/")
def get_employees(session: Session = Depends(get_session)):
    try:
        employees = session.exec(select(Employee)).all()
        return {"status": 200, "data": employees}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Détail employé
# GET /employees/{id}
# -------------------------------
@router.get("/{employee_id}")
def get_employee(employee_id: int, session: Session = Depends(get_session)):
    try:
        employee = session.get(Employee, employee_id)
        if not employee:
            return {"status": 400, "data": []}
        return {"status": 200, "data": employee}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Créer employé
# POST /employees
# -------------------------------
@router.post("/")
def create_employee(employee: Employee, session: Session = Depends(get_session)):
    try:
        session.add(employee)
        session.commit()
        session.refresh(employee)
        return {"status": 200, "data": employee}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier employé
# PUT /employees/{id}
# -------------------------------
@router.put("/{employee_id}")
def update_employee(employee_id: int, employee_data: Employee, session: Session = Depends(get_session)):
    try:
        employee = session.get(Employee, employee_id)
        if not employee:
            return {"status": 400, "data": []}
        employee.nom = employee_data.nom
        employee.identifiant_ui = employee_data.identifiant_ui
        employee.role = employee_data.role
        employee.actif = employee_data.actif
        session.add(employee)
        session.commit()
        session.refresh(employee)
        return {"status": 200, "data": employee}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer employé
# DELETE /employees/{id}
# -------------------------------
@router.delete("/{employee_id}")
def delete_employee(employee_id: int, session: Session = Depends(get_session)):
    try:
        employee = session.get(Employee, employee_id)
        if not employee:
            return {"status": 400, "data": []}
        session.delete(employee)
        session.commit()
        return {"status": 200, "data": {"message": "Employee deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Historique 14 jours
# GET /employees/{id}/history
# -------------------------------
@router.get("/{employee_id}/history")
def employee_history(employee_id: int, session: Session = Depends(get_session)):
    try:
        employee = session.get(Employee, employee_id)
        if not employee:
            return {"status": 400, "data": []}

        today = datetime.now()
        start_date = today - timedelta(days=14)
        
        logs = session.exec(
            select(production_logs)
            .where(production_logs.employee_id == employee_id)
            .where(production_logs.debut_tache >= start_date)
        ).all()
        
        total_pieces = sum(log.pieces_produites for log in logs)
        total_sets = sum(log.sets_produits for log in logs)
        avg_rendement = sum(log.rendement_pct for log in logs) / len(logs) if logs else 0

        return {"status": 200, "data": {
            "employee": employee,
            "logs": logs,
            "stats": {
                "total_pieces": total_pieces,
                "total_sets": total_sets,
                "avg_rendement": avg_rendement
            }
        }}
    except Exception as e:
        return {"status": 400, "data": []}
