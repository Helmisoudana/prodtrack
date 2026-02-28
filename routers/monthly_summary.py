# routers/monthly_summary.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from models.monthly_summary import MonthlySummary
from database.session import get_session
from scheduler.monthly_job import generate_monthly_summary

router = APIRouter(prefix="/monthly-summaries", tags=["Monthly Summaries"])

# GET /monthly-summaries
@router.get("")
def get_all_summaries(session: Session = Depends(get_session)):
    try:
        summaries = session.exec(select(MonthlySummary).order_by(MonthlySummary.periode.desc()).limit(4)).all()
        return {"status": 200, "data": summaries}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /monthly-summaries/{periode}  ex: 2025-01
@router.get("/{periode}")
def get_summary_by_periode(periode: str, session: Session = Depends(get_session)):
    try:
        summary = session.exec(
            select(MonthlySummary).where(MonthlySummary.periode == periode)
        ).first()
        if not summary:
            return {"status": 404, "data": [], "error": f"Aucun summary pour {periode}"}
        return {"status": 200, "data": summary}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# POST /monthly-summaries/generate  → déclencher manuellement
@router.post("/generate")
def trigger_generate():
    try:
        generate_monthly_summary()
        return {"status": 200, "data": {"message": "Summary généré avec succès"}}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}