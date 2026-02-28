# scheduler/monthly_job.py
from sqlmodel import Session, select
from datetime import datetime
from calendar import monthrange

from database.session import engine
from models.employee import employee
from models.production_log import FactoryLog
from models.machine import Machine
from models.monthly_summary import MonthlySummary
from scheduler.fatigue_helper import parse_float, calc_fatigue_usine, get_niveau

COMPLETED = "Completee"
INTERRUPTED = "Interrompue"

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

def generate_monthly_summary():
    now = datetime.now()

    if now.month == 1:
        year, month = now.year - 1, 12
    else:
        year, month = now.year, now.month - 1

    periode = f"{year}-{month:02d}"
    debut = datetime(year, month, 1)
    fin   = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)

    print(f"[Scheduler] Génération monthly summary pour {periode}...")

    with Session(engine) as session:
        existing = session.exec(
            select(MonthlySummary).where(MonthlySummary.periode == periode)
        ).first()
        if existing:
            print(f"[Scheduler] Summary {periode} déjà existant, skip.")
            return

        machines  = session.exec(select(Machine)).all()
        employees = session.exec(select(employee)).all()
        machine_map = {m.machine_id: parse_float(m.temps_par_unite_min) for m in machines}

        all_logs = session.exec(select(FactoryLog)).all()

        def in_periode(log):
            try:
                dt = datetime.fromisoformat(str(log.tag_event_start))
                return debut <= dt <= fin
            except:
                return False

        logs = [l for l in all_logs if in_periode(l)]

        if not logs:
            print(f"[Scheduler] Aucun log pour {periode}.")
            return

        completed   = [l for l in logs if l.task_status == COMPLETED]
        interrupted = [l for l in logs if l.task_status == INTERRUPTED]
        anomalies   = [l for l in logs if l.anomaly_flag == 1]

        durations    = [parse_float(l.task_duration_min) for l in completed if l.task_duration_min]
        avg_duration = sum(durations) / len(durations) if durations else 0
        taux_anomalie = (len(anomalies) / len(logs) * 100) if logs else 0
        rendement_global = calc_rendement(logs, machine_map)

        # Rendement par shift
        shifts_map = {"Matin": [], "Jour": [], "Nuit": []}
        for log in logs:
            s = str(log.shift or "").strip()
            if s in shifts_map:
                shifts_map[s].append(log)

        # Employés
        actifs   = [e for e in employees if e.statut_presence == "En_travail"]
        absents  = [e for e in employees if e.statut_presence == "Absent"]
        en_conge = [e for e in employees if e.statut_presence == "En_conge"]
        machines_en_panne = [m for m in machines if m.etat_machine == "En panne"]

        # Fatigue globale usine
        fatigue = calc_fatigue_usine(employees, session, machine_map)

        summary = MonthlySummary(
            periode=periode,
            date_generation=datetime.now().isoformat(),
            rendement_global_pct=rendement_global,
            duree_moyenne_taches_min=round(avg_duration, 2),
            taux_anomalie_pct=round(taux_anomalie, 2),
            total_taches=len(logs),
            taches_completees=len(completed),
            taches_interrompues=len(interrupted),
            total_anomalies=len(anomalies),
            total_employes=len(employees),
            employes_en_travail=len(actifs),
            employes_absents=len(absents),
            employes_en_conge=len(en_conge),
            total_machines=len(machines),
            machines_en_panne=len(machines_en_panne),
            rendement_matin=calc_rendement(shifts_map["Matin"], machine_map),
            rendement_jour=calc_rendement(shifts_map["Jour"], machine_map),
            rendement_nuit=calc_rendement(shifts_map["Nuit"], machine_map),
            score_fatigue_global=fatigue["score"],
            niveau_fatigue_global=fatigue["niveau"],
            employes_fatigue_critique=fatigue["critique"],
            employes_fatigue_eleve=fatigue["eleve"],
            employes_fatigue_moyen=fatigue["moyen"],
            employes_fatigue_faible=fatigue["faible"],
        )

        session.add(summary)
        session.commit()
        print(f"[Scheduler] Monthly summary {periode} enregistré.")