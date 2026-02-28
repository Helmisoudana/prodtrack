# routers/anomaly.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Optional

from models.production_log import FactoryLog
from models.machine import Machine
from models.employee import employee
from database.session import get_session
from ml.anomaly_service import predict_anomaly

router = APIRouter(prefix="/anomaly", tags=["Anomaly Detection"])


# POST /anomaly/predict/{log_id}
# Prédire anomalie pour un log existant
@router.post("/predict/{log_id}")
def predict_single(log_id: str, session: Session = Depends(get_session)):
    try:
        log = session.get(FactoryLog, log_id)
        if not log:
            return {"status": 404, "data": [], "error": "Log non trouvé"}

        machine = session.get(Machine, log.machine_id) if log.machine_id else None
        emp     = session.get(employee, log.employee_id) if log.employee_id else None

        result = predict_anomaly(log, machine, emp)
        return {
            "status": 200,
            "data": {
                "log_id":      log_id,
                "employee_id": log.employee_id,
                "machine_id":  log.machine_id,
                "task_name":   log.task_name,
                "prediction":  result
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}


# POST /anomaly/predict-batch
# Prédire sur les N derniers logs
@router.post("/predict-batch")
def predict_batch(
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session)
):
    try:
        logs     = session.exec(select(FactoryLog).limit(limit)).all()
        machines = {m.machine_id: m for m in session.exec(select(Machine)).all()}
        emps     = {e.employee_id: e for e in session.exec(select(employee)).all()}

        results      = []
        total_anomalies = 0

        for log in logs:
            machine = machines.get(log.machine_id)
            emp     = emps.get(log.employee_id)
            pred    = predict_anomaly(log, machine, emp)

            if pred["is_anomaly"]:
                total_anomalies += 1

            results.append({
                "log_id":      log.log_id,
                "employee_id": log.employee_id,
                "machine_id":  log.machine_id,
                "task_name":   log.task_name,
                "prediction":  pred
            })

        return {
            "status": 200,
            "data": {
                "total_analysed":   len(results),
                "total_anomalies":  total_anomalies,
                "taux_anomalie_pct": round(total_anomalies / len(results) * 100, 2) if results else 0,
                "results":          results
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}


# GET /anomaly/stats
# Stats globales des anomalies détectées par le modèle
@router.get("/stats")
def anomaly_stats(session: Session = Depends(get_session)):
    try:
        logs     = session.exec(select(FactoryLog)).all()
        machines = {m.machine_id: m for m in session.exec(select(Machine)).all()}
        emps     = {e.employee_id: e for e in session.exec(select(employee)).all()}

        total        = len(logs)
        anomalies    = []
        par_machine  = {}
        par_employe  = {}

        for log in logs:
            machine = machines.get(log.machine_id)
            emp     = emps.get(log.employee_id)
            pred    = predict_anomaly(log, machine, emp)

            if pred["is_anomaly"]:
                anomalies.append(log)
                par_machine[log.machine_id]  = par_machine.get(log.machine_id, 0) + 1
                par_employe[log.employee_id] = par_employe.get(log.employee_id, 0) + 1

        # Top 5 machines et employés les plus anormaux
        top_machines = sorted(par_machine.items(), key=lambda x: x[1], reverse=True)[:5]
        top_employes = sorted(par_employe.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "status": 200,
            "data": {
                "total_logs":       total,
                "total_anomalies":  len(anomalies),
                "taux_anomalie_pct": round(len(anomalies) / total * 100, 2) if total else 0,
                "top_machines":     [{"machine_id": k, "anomalies": v} for k, v in top_machines],
                "top_employes":     [{"employee_id": k, "anomalies": v} for k, v in top_employes],
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}