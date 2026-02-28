# routers/dispatching.py
from fastapi import APIRouter, HTTPException, Query
from services.dispatching_service import (
    run_dispatching_hungarian,
    worst_real_dispatching
)

router = APIRouter(
    prefix="/api/dispatching",
    tags=["Dispatching"]
)



@router.get("/hungarian")
async def dispatching_hungarian():
    """
    Lance l'algorithme de dispatching basé sur l'algorithme Hongrois.
    """
    try:
        data = run_dispatching_hungarian()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worst_real")
async def get_worst_real_dispatching(
    day: str = Query(..., description="Date au format YYYY-MM-DD", example="2024-01-15")
):
    """
    Récupère le pire employé par machine/product pour un jour donné.
    
    Args:
        day: Date au format YYYY-MM-DD (ex: "2024-01-15")
    """
    if not day:
        raise HTTPException(
            status_code=400, 
            detail="Veuillez fournir le paramètre day au format YYYY-MM-DD"
        )
    
    try:
        results = worst_real_dispatching(day)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))