# routes/assignment.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.assignment import Assignment
from database.session import get_session

router = APIRouter(prefix="/assignments", tags=["Assignments"])

# -------------------------------
# Liste assignments
# GET /assignments
# -------------------------------
@router.get("/")
def get_assignments(session: Session = Depends(get_session)):
    try:
        assignments = session.exec(select(Assignment)).all()
        return {"status": 200, "data": assignments}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Détail assignment
# GET /assignments/{assignment_id}
# -------------------------------
@router.get("/{assignment_id}")
def get_assignment(assignment_id: int, session: Session = Depends(get_session)):
    try:
        assignment = session.get(Assignment, assignment_id)
        if not assignment:
            return {"status": 400, "data": []}
        return {"status": 200, "data": assignment}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Créer assignment
# POST /assignments
# -------------------------------
@router.post("/")
def create_assignment(assignment_data: Assignment, session: Session = Depends(get_session)):
    try:
        session.add(assignment_data)
        session.commit()
        session.refresh(assignment_data)
        return {"status": 200, "data": assignment_data}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier assignment
# PUT /assignments/{assignment_id}
# -------------------------------
@router.put("/{assignment_id}")
def update_assignment(assignment_id: int, assignment_data: Assignment, session: Session = Depends(get_session)):
    try:
        assignment = session.get(Assignment, assignment_id)
        if not assignment:
            return {"status": 400, "data": []}

        assignment.employee_id = assignment_data.employee_id
        assignment.machine_id = assignment_data.machine_id
        assignment.task_id = assignment_data.task_id
        assignment.shift_id = assignment_data.shift_id
        assignment.start_date = assignment_data.start_date
        assignment.end_date = assignment_data.end_date
        assignment.justification = assignment_data.justification

        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        return {"status": 200, "data": assignment}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer assignment
# DELETE /assignments/{assignment_id}
# -------------------------------
@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, session: Session = Depends(get_session)):
    try:
        assignment = session.get(Assignment, assignment_id)
        if not assignment:
            return {"status": 400, "data": []}
        session.delete(assignment)
        session.commit()
        return {"status": 200, "data": {"message": "Assignment deleted successfully"}}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}
