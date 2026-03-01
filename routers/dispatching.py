# routers/dispatching.py
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session
from database.session import get_session
from services.dispatching_service import (
    run_dispatching_hungarian,
    worst_real_dispatching
)

router = APIRouter(
    prefix="/api/dispatching",
    tags=["Dispatching"]
)


@router.get("/hungarian")
async def dispatching_hungarian(session: Session = Depends(get_session)):
    """
    Lance l'algorithme de dispatching basé sur l'algorithme Hongrois.
    """
    try:
        data = run_dispatching_hungarian(session)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worst_real")
async def get_worst_real_dispatching(
    day: str = Query(..., description="Date au format YYYY-MM-DD", example="2024-01-15"),
    session: Session = Depends(get_session)
):
    """
    Récupère le pire employé par machine/product pour un jour donné.
    """
    try:
        results = worst_real_dispatching(day, session)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))