# routes/employee.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from models.employee import employee
from database.session import get_session

router = APIRouter(prefix="/employees", tags=["Employees"])

# GET /employees?page=1&limit=20
@router.get("")
def get_employees(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        offset = (page - 1) * limit
        total = len(session.exec(select(employee)).all())
        employees = session.exec(select(employee).offset(offset).limit(limit)).all()
        return {
            "status": 200,
            "data": employees,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /employees/{id}
@router.get("/{employee_id}")
def get_employee(employee_id: str, session: Session = Depends(get_session)):
    try:
        emp = session.get(employee, employee_id)
        if not emp:
            return {"status": 400, "data": []}
        return {"status": 200, "data": emp}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# POST /employees
@router.post("")
def create_employee(emp: employee, session: Session = Depends(get_session)):
    try:
        session.add(emp)
        session.commit()
        session.refresh(emp)
        return {"status": 200, "data": emp}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# PUT /employees/{id}
@router.put("/{employee_id}")
def update_employee(employee_id: str, emp_data: employee, session: Session = Depends(get_session)):
    try:
        emp = session.get(employee, employee_id)
        if not emp:
            return {"status": 400, "data": []}

        update_data = emp_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(emp, key, value)

        session.add(emp)
        session.commit()
        session.refresh(emp)
        return {"status": 200, "data": emp}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}

# DELETE /employees/{id}
@router.delete("/{employee_id}")
def delete_employee(employee_id: str, session: Session = Depends(get_session)):
    try:
        emp = session.get(employee, employee_id)
        if not emp:
            return {"status": 400, "data": []}
        session.delete(emp)
        session.commit()
        return {"status": 200, "data": {"message": "Employee deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}