# routers/shift_summary.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Optional

from models.shift_summary import ShiftSummary
from database.session import get_session
from scheduler.shift_job import generate_shift_summary

router = APIRouter(prefix="/shift-summaries", tags=["Shift Summaries"])

# GET /shift-summaries
@router.get("")
def get_all(
    shift: Optional[str] = Query(None),  # filtrer par Matin/Jour/Nuit
    session: Session = Depends(get_session)
):
    try:
        query = select(ShiftSummary).order_by(ShiftSummary.date.desc()).limit(3)
        if shift:
            query = query.where(ShiftSummary.shift == shift)
        summaries = session.exec(query).all()
        return {"status": 200, "data": summaries}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

@router.get("/last10days")
def get_all_10_days(
    shift: Optional[str] = Query(None),  # filtrer par Matin/Jour/Nuit
    session: Session = Depends(get_session)
):
    try:
        query = select(ShiftSummary).order_by(ShiftSummary.date.desc()).limit(30)
        if shift:
            query = query.where(ShiftSummary.shift == shift)
        summaries = session.exec(query).all()
        return {"status": 200, "data": summaries}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /shift-summaries/{date}  ex: 2025-01-15
@router.get("/{date}")
def get_by_date(date: str, session: Session = Depends(get_session)):
    try:
        summaries = session.exec(
            select(ShiftSummary).where(ShiftSummary.date == date)
        ).all()
        if not summaries:
            return {"status": 404, "data": [], "error": f"Aucun summary pour {date}"}
        return {"status": 200, "data": summaries}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# POST /shift-summaries/generate/{shift}  → déclencher manuellement
@router.post("/generate/{shift}")
def trigger_generate(shift: str):
    try:
        if shift not in ["Matin", "Jour", "Nuit"]:
            return {"status": 400, "data": [], "error": "Shift invalide. Valeurs: Matin, Jour, Nuit"}
        generate_shift_summary(shift)
        return {"status": 200, "data": {"message": f"Shift summary {shift} généré avec succès"}}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}