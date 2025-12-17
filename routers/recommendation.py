# routes/recommendation.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.recommendation import Recommendation
from models.assignment import Assignment
from database.session import get_session

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# -------------------------------
# Liste recommandations
# GET /recommendations
# -------------------------------
@router.get("/")
def get_recommendations(session: Session = Depends(get_session)):
    try:
        recommendations = session.exec(select(Recommendation)).all()
        return {"status": 200, "data": recommendations}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Détail recommandation
# GET /recommendations/{id}
# -------------------------------
@router.get("/{rec_id}")
def get_recommendation(rec_id: int, session: Session = Depends(get_session)):
    try:
        rec = session.get(Recommendation, rec_id)
        if not rec:
            return {"status": 400, "data": []}
        return {"status": 200, "data": rec}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Appliquer recommandation
# PUT /recommendations/{id}/apply
# -------------------------------
@router.put("/{rec_id}/apply")
def apply_recommendation(rec_id: int, session: Session = Depends(get_session)):
    try:
        rec = session.get(Recommendation, rec_id)
        if not rec:
            return {"status": 400, "data": []}

        # Créer ou mettre à jour assignment selon recommandation
        assignment = Assignment(
            employee_id=rec.employee_id,
            machine_id=rec.machine_id,
            task_id=rec.task_id,
            shift_id=rec.shift_id,
            start_date=rec.start_date,
            end_date=rec.end_date,
            justification="IA Applied"
        )
        session.add(assignment)
        # Optionnel : marquer recommandation comme appliquée
        rec.status = "applied"
        session.add(rec)

        session.commit()
        session.refresh(assignment)
        return {"status": 200, "data": assignment}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Refuser recommandation
# PUT /recommendations/{id}/reject
# -------------------------------
@router.put("/{rec_id}/reject")
def reject_recommendation(rec_id: int, session: Session = Depends(get_session)):
    try:
        rec = session.get(Recommendation, rec_id)
        if not rec:
            return {"status": 400, "data": []}
        rec.status = "rejected"
        session.add(rec)
        session.commit()
        session.refresh(rec)
        return {"status": 200, "data": rec}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}
