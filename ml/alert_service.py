# ml/alert_service.py
from sqlmodel import Session, select
from datetime import datetime

from models.production_log import FactoryLog
from models.machine import Machine
from models.employee import employee
from models.alert import Alert
from ml.anomaly_service import predict_anomaly

def parse_float(val) -> float:
    if val is None: return 0.0
    try:    return float(str(val).replace(",", "."))
    except: return 0.0

def check_and_save_alert(log: FactoryLog, session: Session) -> dict:
    """
    Appelé à chaque nouveau log ajouté.
    Prédit l'anomalie et sauvegarde une alerte si détectée.
    """
    try:
        # Vérifier si alerte déjà existante pour ce log
        existing = session.exec(
            select(Alert).where(Alert.log_id == log.log_id)
        ).first()
        if existing:
            return {"skipped": True, "reason": "Alerte déjà existante"}

        # Charger machine et employé
        machine = session.get(Machine, log.machine_id)   if log.machine_id   else None
        emp     = session.get(employee, log.employee_id) if log.employee_id  else None

        # Prédiction
        pred = predict_anomaly(log, machine, emp)

        # Sauvegarder alerte seulement si anomalie détectée
        # OU si le flag original est déjà 1
        original_flag = log.anomaly_flag or 0
        if pred["is_anomaly"] == 1 or original_flag == 1:
            alert = Alert(
                log_id=log.log_id,
                employee_id=log.employee_id,
                machine_id=log.machine_id,
                task_name=log.task_name,
                shift=log.shift,
                date_detection=datetime.now().isoformat(),
                is_anomaly=pred["is_anomaly"],
                confidence=pred["confidence"],
                score_raw=pred["score_raw"],
                label=pred["label"],
                task_duration_min=parse_float(log.task_duration_min),
                task_status=log.task_status,
                anomaly_flag_original=original_flag,
                statut="Nouvelle"
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return {"alert_created": True, "alert_id": alert.id, "prediction": pred}

        return {"alert_created": False, "prediction": pred}

    except Exception as e:
        return {"alert_created": False, "error": str(e)}