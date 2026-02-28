# scheduler/shift_job.py
from sqlmodel import Session, select
from datetime import datetime, timedelta

from database.session import engine
from models.production_log import FactoryLog
from models.machine import Machine
from models.employee import employee
from models.shift_summary import ShiftSummary
from scheduler.fatigue_helper import parse_float, calc_fatigue_score, get_niveau

COMPLETED = "Completee"
INTERRUPTED = "Interrompue"

SHIFTS = {
    "Matin": (6, 14),
    "Jour":  (14, 22),
    "Nuit":  (22, 6),
}

def calc_rendement(logs, machine_map):
    rendements = []
    for log in logs:
        if log.task_status != COMPLETED:
            continue
        temps_reel = parse_float(log.task_duration_min)
        temps_theorique = machine_map.get(log.machine_id, 0)
        if temps_theorique > 0 and temps_reel > 0:
            rendements.append(min((temps_theorique / temps_reel) * 100, 100))
    return round(sum(rendements) / len(rendements), 2) if rendements else 0.0

def generate_shift_summary(shift_name: str):
    now = datetime.now()

    if shift_name == "Matin":
        date_ref = now.date()
        debut = datetime(date_ref.year, date_ref.month, date_ref.day, 6, 0, 0)
        fin   = datetime(date_ref.year, date_ref.month, date_ref.day, 14, 0, 0)
    elif shift_name == "Jour":
        date_ref = now.date()
        debut = datetime(date_ref.year, date_ref.month, date_ref.day, 14, 0, 0)
        fin   = datetime(date_ref.year, date_ref.month, date_ref.day, 22, 0, 0)
    elif shift_name == "Nuit":
        date_ref = (now - timedelta(days=1)).date()
        debut = datetime(date_ref.year, date_ref.month, date_ref.day, 22, 0, 0)
        fin   = datetime(now.year, now.month, now.day, 6, 0, 0)

    date_str = str(date_ref)

    with Session(engine) as session:
        existing = session.exec(
            select(ShiftSummary)
            .where(ShiftSummary.date == date_str)
            .where(ShiftSummary.shift == shift_name)
        ).first()
        if existing:
            print(f"[Scheduler] Shift {shift_name} {date_str} déjà existant, skip.")
            return

        machines = session.exec(select(Machine)).all()
        machine_map = {m.machine_id: parse_float(m.temps_par_unite_min) for m in machines}

        all_logs = session.exec(select(FactoryLog)).all()

        def in_shift(log):
            try:
                dt = datetime.fromisoformat(str(log.tag_event_start))
                return debut <= dt < fin
            except:
                return False

        logs = [l for l in all_logs if in_shift(l)]

        if not logs:
            print(f"[Scheduler] Aucun log pour shift {shift_name} {date_str}.")
            return

        completed   = [l for l in logs if l.task_status == COMPLETED]
        interrupted = [l for l in logs if l.task_status == INTERRUPTED]
        anomalies   = [l for l in logs if l.anomaly_flag == 1]

        durations    = [parse_float(l.task_duration_min) for l in completed if l.task_duration_min]
        avg_duration = sum(durations) / len(durations) if durations else 0
        taux_anomalie = (len(anomalies) / len(logs) * 100) if logs else 0
        rendement = calc_rendement(logs, machine_map)

        # Employés de ce shift
        employee_ids = list(set(l.employee_id for l in logs if l.employee_id))
        employes_shift = session.exec(
            select(employee).where(employee.employee_id.in_(employee_ids))
        ).all()

        # Fatigue des employés de ce shift
        critique, eleve, moyen, faible = 0, 0, 0, 0
        scores_fatigue = []
        for emp in employes_shift:
            emp_logs = [l for l in logs if l.employee_id == emp.employee_id]
            fatigue = calc_fatigue_score(emp, emp_logs, machine_map)
            scores_fatigue.append(fatigue["score"])
            if fatigue["niveau"] == "Critique":  critique += 1
            elif fatigue["niveau"] == "Eleve":   eleve += 1
            elif fatigue["niveau"] == "Moyen":   moyen += 1
            else:                                faible += 1

        score_fatigue_shift = round(sum(scores_fatigue) / len(scores_fatigue), 2) if scores_fatigue else 0.0
        niveau_fatigue_shift = get_niveau(score_fatigue_shift)

        summary = ShiftSummary(
            date=date_str,
            shift=shift_name,
            date_generation=datetime.now().isoformat(),
            rendement_pct=rendement,
            duree_moyenne_min=round(avg_duration, 2),
            taux_anomalie_pct=round(taux_anomalie, 2),
            total_taches=len(logs),
            taches_completees=len(completed),
            taches_interrompues=len(interrupted),
            total_anomalies=len(anomalies),
            total_employes_shift=len(employes_shift),
            score_fatigue_shift=score_fatigue_shift,
            niveau_fatigue_shift=niveau_fatigue_shift,
            employes_fatigue_critique=critique,
            employes_fatigue_eleve=eleve,
            employes_fatigue_moyen=moyen,
            employes_fatigue_faible=faible,
        )

        session.add(summary)
        session.commit()
        print(f"[Scheduler] Shift summary {shift_name} {date_str} enregistré.")