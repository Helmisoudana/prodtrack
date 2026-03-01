# routes/kpis.py
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Optional

from models.employee import employee
from models.production_log import FactoryLog
from models.machine import Machine
from database.session import get_session

router = APIRouter(prefix="/kpis", tags=["KPIs"])

# Helper pour parser les floats avec virgule
def parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", "."))
    except:
        return 0.0

# Statuts valides
COMPLETED = "Completee"
INTERRUPTED = "Interrompue"


# GET /kpis/rendement-global
@router.get("/rendement-global")
def get_rendement_global(session: Session = Depends(get_session)):
    try:
        logs = session.exec(select(FactoryLog)).all()
        machines = session.exec(select(Machine)).all()

        machine_map = {m.machine_id: parse_float(m.temps_par_unite_min) for m in machines}

        total_logs = len(logs)
        completed = [l for l in logs if l.task_status == COMPLETED]
        interrupted = [l for l in logs if l.task_status == INTERRUPTED]
        anomalies = [l for l in logs if l.anomaly_flag == 1]

        rendements = []
        for log in completed:
            temps_reel = parse_float(log.task_duration_min)
            temps_theorique = machine_map.get(log.machine_id, 0)
            if temps_theorique > 0 and temps_reel > 0:
                r = (temps_theorique / temps_reel) * 100
                rendements.append(min(r, 100))

        rendement_global = sum(rendements) / len(rendements) if rendements else 0

        durations = [parse_float(l.task_duration_min) for l in completed if l.task_duration_min]
        avg_duration = sum(durations) / len(durations) if durations else 0
        taux_anomalie = (len(anomalies) / total_logs * 100) if total_logs else 0

        return {
            "status": 200,
            "data": {
                "total_logs": total_logs,
                "taches_completees": len(completed),
                "taches_interrompues": len(interrupted),
                "total_anomalies": len(anomalies),
                "taux_anomalie_pct": round(taux_anomalie, 2),
                "rendement_global_pct": round(rendement_global, 2),
                "duree_moyenne_min": round(avg_duration, 2),
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}


# GET /kpis/rendement-par-employe
@router.get("/rendement-par-employe")
def get_rendement_par_employe(
    employee_id: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    try:
        machines = session.exec(select(Machine)).all()
        machine_map = {m.machine_id: parse_float(m.temps_par_unite_min) for m in machines}

        emp_query = select(employee)
        if employee_id:
            emp_query = emp_query.where(employee.employee_id == employee_id)
        employees = session.exec(emp_query).all()

        result = []
        for emp in employees:
            logs = session.exec(
                select(FactoryLog).where(FactoryLog.employee_id == emp.employee_id)
            ).all()

            total = len(logs)
            if total == 0:
                continue

            completed = [l for l in logs if l.task_status == COMPLETED]
            interrupted = [l for l in logs if l.task_status == INTERRUPTED]
            anomalies = [l for l in logs if l.anomaly_flag == 1]

            rendements = []
            for log in completed:
                temps_reel = parse_float(log.task_duration_min)
                temps_theorique = machine_map.get(log.machine_id, 0)
                if temps_theorique > 0 and temps_reel > 0:
                    r = (temps_theorique / temps_reel) * 100
                    rendements.append(min(r, 100))

            rendement = sum(rendements) / len(rendements) if rendements else 0
            durations = [parse_float(l.task_duration_min) for l in completed if l.task_duration_min]
            avg_duration = sum(durations) / len(durations) if durations else 0
            taux_anomalie = (len(anomalies) / total * 100) if total else 0

            result.append({
                "employee_id": emp.employee_id,
                "nom": emp.nom,
                "prenom": emp.prenom,
                "poste": emp.poste,
                "departement": emp.departement,
                "shift_travail": emp.shift_travail,
                "statut_presence": emp.statut_presence,
                "performance_moyenne": parse_float(emp.performance_moyenne),
                "taux_rendement_db": parse_float(emp.taux_rendement),
                "total_taches": total,
                "taches_completees": len(completed),
                "taches_interrompues": len(interrupted),
                "total_anomalies": len(anomalies),
                "taux_anomalie_pct": round(taux_anomalie, 2),
                "rendement_calcule_pct": round(rendement, 2),
                "duree_moyenne_min": round(avg_duration, 2),
            })

        result.sort(key=lambda x: x["rendement_calcule_pct"], reverse=True)
        return {"status": 200, "data": result}
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}

# GET /kpis/rendement-employe/{employee_id}
@router.get("/rendement-employe/{employee_id}")
def get_rendement_employe_by_id(
    employee_id: str,
    session: Session = Depends(get_session)
):
    try:
        # Vérifier si employé existe
        emp = session.exec(
            select(employee).where(employee.employee_id == employee_id)
        ).first()

        if not emp:
            return {"status": 404, "error": "Employé non trouvé"}

        # Récupérer machines
        machines = session.exec(select(Machine)).all()
        machine_map = {m.machine_id: parse_float(m.temps_par_unite_min) for m in machines}

        # Logs de l'employé
        logs = session.exec(
            select(FactoryLog).where(FactoryLog.employee_id == employee_id)
        ).all()

        total = len(logs)
        if total == 0:
            return {
                "status": 200,
                "data": {
                    "employee_id": employee_id,
                    "message": "Aucune tâche trouvée pour cet employé"
                }
            }

        completed = [l for l in logs if l.task_status == COMPLETED]
        interrupted = [l for l in logs if l.task_status == INTERRUPTED]
        anomalies = [l for l in logs if l.anomaly_flag == 1]

        # Calcul rendement
        rendements = []
        for log in completed:
            temps_reel = parse_float(log.task_duration_min)
            temps_theorique = machine_map.get(log.machine_id, 0)

            if temps_theorique > 0 and temps_reel > 0:
                r = (temps_theorique / temps_reel) * 100
                rendements.append(min(r, 100))

        rendement = sum(rendements) / len(rendements) if rendements else 0

        durations = [parse_float(l.task_duration_min) for l in completed if l.task_duration_min]
        avg_duration = sum(durations) / len(durations) if durations else 0

        taux_anomalie = (len(anomalies) / total * 100) if total else 0

        return {
            "status": 200,
            "data": {
                "employee_id": emp.employee_id,
                "nom": emp.nom,
                "prenom": emp.prenom,
                "poste": emp.poste,
                "departement": emp.departement,
                "shift_travail": emp.shift_travail,
                "statut_presence": emp.statut_presence,
                "performance_moyenne_db": parse_float(emp.performance_moyenne),
                "taux_rendement_db": parse_float(emp.taux_rendement),
                "total_taches": total,
                "taches_completees": len(completed),
                "taches_interrompues": len(interrupted),
                "total_anomalies": len(anomalies),
                "taux_anomalie_pct": round(taux_anomalie, 2),
                "rendement_calcule_pct": round(rendement, 2),
                "duree_moyenne_min": round(avg_duration, 2),
            }
        }

    except Exception as e:
        return {"status": 400, "error": str(e)}
# GET /kpis/duree-moyenne-taches
@router.get("/duree-moyenne-taches")
def get_duree_moyenne_taches(session: Session = Depends(get_session)):
    try:
        logs = session.exec(
            select(FactoryLog).where(FactoryLog.task_status == COMPLETED)
        ).all()

        if not logs:
            return {"status": 200, "data": {"duree_moyenne_globale_min": 0, "par_tache": []}}

        all_durations = [parse_float(l.task_duration_min) for l in logs if l.task_duration_min]
        avg_global = sum(all_durations) / len(all_durations) if all_durations else 0

        tasks = {}
        for log in logs:
            name = log.task_name or "Inconnu"
            if name not in tasks:
                tasks[name] = []
            if log.task_duration_min:
                tasks[name].append(parse_float(log.task_duration_min))

        par_tache = []
        for task_name, durations in tasks.items():
            if durations:
                par_tache.append({
                    "task_name": task_name,
                    "nb_executions": len(durations),
                    "duree_moyenne_min": round(sum(durations) / len(durations), 2),
                    "duree_min_min": round(min(durations), 2),
                    "duree_max_min": round(max(durations), 2),
                })

        par_tache.sort(key=lambda x: x["duree_moyenne_min"], reverse=True)

        return {
            "status": 200,
            "data": {
                "duree_moyenne_globale_min": round(avg_global, 2),
                "par_tache": par_tache
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}


# GET /kpis/summary
@router.get("/summary")
def get_summary(session: Session = Depends(get_session)):
    try:
        logs = session.exec(select(FactoryLog)).all()
        employees = session.exec(select(employee)).all()
        machines = session.exec(select(Machine)).all()
        machine_map = {m.machine_id: parse_float(m.temps_par_unite_min) for m in machines}

        total_logs = len(logs)
        completed = [l for l in logs if l.task_status == COMPLETED]
        interrupted = [l for l in logs if l.task_status == INTERRUPTED]
        anomalies = [l for l in logs if l.anomaly_flag == 1]

        rendements = []
        for log in completed:
            temps_reel = parse_float(log.task_duration_min)
            temps_theorique = machine_map.get(log.machine_id, 0)
            if temps_theorique > 0 and temps_reel > 0:
                rendements.append(min((temps_theorique / temps_reel) * 100, 100))

        rendement_global = sum(rendements) / len(rendements) if rendements else 0
        durations = [parse_float(l.task_duration_min) for l in completed if l.task_duration_min]
        avg_duration = sum(durations) / len(durations) if durations else 0
        taux_anomalie = (len(anomalies) / total_logs * 100) if total_logs else 0

        actifs = [e for e in employees if e.statut_presence == "En_travail"]
        absents = [e for e in employees if e.statut_presence == "Absent"]
        en_conge = [e for e in employees if e.statut_presence == "En_conge"]
        machines_en_panne = [m for m in machines if m.etat_machine == "En panne"]

        return {
            "status": 200,
            "data": {
                "rendement_global_pct": round(rendement_global, 2),
                "taux_anomalie_pct": round(taux_anomalie, 2),
                "duree_moyenne_taches_min": round(avg_duration, 2),
                "total_employes": len(employees),
                "employes_en_travail": len(actifs),
                "employes_absents": len(absents),
                "employes_en_conge": len(en_conge),
                "total_machines": len(machines),
                "machines_en_panne": len(machines_en_panne),
                "total_taches": total_logs,
                "taches_completees": len(completed),
                "taches_interrompues": len(interrupted),
                "total_anomalies": len(anomalies),
            }
        }
    except Exception as e:
        return {"status": 400, "data": [], "error": str(e)}