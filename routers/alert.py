# routers/alert.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Optional

from models.alert import Alert
from database.session import get_session

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# GET /alerts
@router.get("")
def get_alerts(
    statut: Optional[str] = Query(None),   # Nouvelle | Vue | Traitee
    machine_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session)
):
    try:
        query = select(Alert).order_by(Alert.date_detection.desc())
        if statut:      query = query.where(Alert.statut == statut)
        if machine_id:  query = query.where(Alert.machine_id == machine_id)
        if employee_id: query = query.where(Alert.employee_id == employee_id)

        total  = len(session.exec(query).all())
        offset = (page - 1) * limit
        alerts = session.exec(query.offset(offset).limit(limit)).all()

        return {
            "status": 200,
            "data": alerts,
            "pagination": {"page": page, "limit": limit, "total": total,
                           "pages": (total + limit - 1) // limit}
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /alerts/stats
@router.get("/stats")
def get_alert_stats(session: Session = Depends(get_session)):
    try:
        alerts    = session.exec(select(Alert)).all()
        total     = len(alerts)
        nouvelles = len([a for a in alerts if a.statut == "Nouvelle"])
        vues      = len([a for a in alerts if a.statut == "Vue"])
        traitees  = len([a for a in alerts if a.statut == "Traitee"])

        par_machine  = {}
        par_employe  = {}
        for a in alerts:
            par_machine[a.machine_id]   = par_machine.get(a.machine_id, 0) + 1
            par_employe[a.employee_id]  = par_employe.get(a.employee_id, 0) + 1

        top_machines = sorted(par_machine.items(), key=lambda x: x[1], reverse=True)[:5]
        top_employes = sorted(par_employe.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "status": 200,
            "data": {
                "total": total,
                "nouvelles": nouvelles,
                "vues": vues,
                "traitees": traitees,
                "top_machines": [{"machine_id": k, "alerts": v} for k, v in top_machines],
                "top_employes": [{"employee_id": k, "alerts": v} for k, v in top_employes],
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# PATCH /alerts/{id}/statut  → marquer Vue ou Traitee
@router.patch("/{alert_id}/statut")
def update_statut(
    alert_id: int,
    statut: str = Query(...),   # Vue | Traitee
    session: Session = Depends(get_session)
):
    try:
        if statut not in ["Vue", "Traitee"]:
            return {"status": 400, "data": [], "error": "Statut invalide. Valeurs: Vue, Traitee"}

        alert = session.get(Alert, alert_id)
        if not alert:
            return {"status": 404, "data": []}

        alert.statut = statut
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return {"status": 200, "data": alert}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": [], "error": str(e)}