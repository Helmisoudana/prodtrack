# scheduler/fatigue_helper.py
from models.production_log import FactoryLog
from models.machine import Machine
from sqlmodel import Session, select

COMPLETED = "Completee"

def parse_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", "."))
    except:
        return 0.0

def get_niveau(score: float) -> str:
    if score >= 70:   return "Critique"
    elif score >= 50: return "Eleve"
    elif score >= 30: return "Moyen"
    else:             return "Faible"

def calc_fatigue_score(emp, logs, machine_map) -> dict:
    score = 0

    # Shift
    shift = str(emp.shift_travail or "").strip()
    if shift == "Nuit":       score += 30
    elif shift == "Rotation": score += 15

    # Age
    age = emp.age or 0
    if age > 50:   score += 20
    elif age > 40: score += 10

    # Ancienneté
    anciennete = emp.anciennete_annees or 0
    if anciennete > 20:   score += 15
    elif anciennete > 10: score += 8

    # Enfants
    enfants = emp.nombre_enfants or 0
    if enfants >= 3:   score += 10
    elif enfants >= 1: score += 5

    # Absences
    absences = emp.heures_absence_mois or 0
    if absences > 30:   score += 15
    elif absences > 15: score += 8

    # Retards
    retards = emp.retards_mois or 0
    if retards > 10:   score += 10
    elif retards > 5:  score += 5

    # Duration ratio
    ratios = []
    for log in logs:
        if log.task_status != COMPLETED:
            continue
        temps_reel = parse_float(log.task_duration_min)
        temps_theorique = machine_map.get(log.machine_id, 0)
        if temps_theorique > 0 and temps_reel > 0:
            ratios.append(temps_reel / temps_theorique)

    avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0
    if avg_ratio > 1.5:   score += 20
    elif avg_ratio > 1.2: score += 10

    return {
        "score": min(score, 100),
        "niveau": get_niveau(score)
    }

def calc_fatigue_usine(employees, session: Session, machine_map: dict) -> dict:
    scores = []
    critique, eleve, moyen, faible = 0, 0, 0, 0

    for emp in employees:
        logs = session.exec(
            select(FactoryLog).where(FactoryLog.employee_id == emp.employee_id)
        ).all()
        fatigue = calc_fatigue_score(emp, logs, machine_map)
        scores.append(fatigue["score"])

        if fatigue["niveau"] == "Critique":  critique += 1
        elif fatigue["niveau"] == "Eleve":   eleve += 1
        elif fatigue["niveau"] == "Moyen":   moyen += 1
        else:                                faible += 1

    score_moyen = round(sum(scores) / len(scores), 2) if scores else 0.0

    return {
        "score": score_moyen,
        "niveau": get_niveau(score_moyen),
        "critique": critique,
        "eleve": eleve,
        "moyen": moyen,
        "faible": faible
    }