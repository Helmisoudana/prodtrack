"""
Seed script for ProdTrack database.
Populates employees (E001-E500), machines (M001-M010), production logs,
alerts, monthly summaries, and shift summaries with realistic textile factory data.

Usage:
    cd Documents/poc-project/prodtrack
    source venv/bin/activate
    python seed.py
"""
import os
import sys
import random
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from sqlmodel import SQLModel, Session
from database.session import engine, init_db
from models.employee import employee
from models.machine import Machine
from models.production_log import FactoryLog
from models.alert import Alert
from models.monthly_summary import MonthlySummary
from models.shift_summary import ShiftSummary

random.seed(42)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
SHIFTS = ["Matin", "Jour", "Nuit"]
STATUT_PRESENCE = ["En_travail", "Absent", "En_conge"]
SEXES = ["M", "F"]
ETAT_CIVIL = ["Celibataire", "Marie", "Divorce"]
NIVEAUX_ETUDE = ["Bac", "Bac+2", "Bac+3", "Bac+5", "CAP", "BEP"]
POSTES = [
    "Operateur tissage", "Operateur teinture", "Operateur coupe",
    "Operateur finition", "Technicien maintenance", "Controleur qualite",
    "Chef d'equipe", "Operateur emballage", "Operateur broderie",
    "Magasinier"
]
DEPARTEMENTS = ["Tissage", "Teinture", "Coupe", "Finition", "Maintenance", "Qualite", "Emballage", "Broderie"]
TYPES_CONTRAT = ["CDI", "CDD", "Interim"]
RISQUES = ["Faible", "Moyen", "Eleve"]

PRENOMS_M = ["Mohamed", "Ahmed", "Ali", "Omar", "Youssef", "Khalil", "Hamza", "Bilal", "Amine", "Rami",
             "Nabil", "Karim", "Sofiane", "Hicham", "Walid", "Rachid", "Tarek", "Fares", "Samir", "Mourad"]
PRENOMS_F = ["Fatima", "Amira", "Sara", "Nour", "Yasmine", "Ines", "Meriem", "Houda", "Leila", "Samia",
             "Rania", "Salma", "Asma", "Rim", "Donia", "Wafa", "Sonia", "Hana", "Lina", "Marwa"]
NOMS = ["Ben Ali", "Trabelsi", "Bouazizi", "Chaabane", "Dridi", "Gharbi", "Hamdi", "Jebali",
        "Karoui", "Laabidi", "Maatoug", "Nasri", "Oueslati", "Riahi", "Saidi", "Tlili",
        "Yahia", "Zouari", "Ferchichi", "Belhadj"]

MACHINE_DEFS = [
    ("M001", "Metier a tisser Jacquard",    "Tissage",       "Tissage",    "Tissage Jacquard",     "metre", 500, 0.58, 290, 4, "Dornier",  "Elevee"),
    ("M002", "Machine teinture Jet",         "Teinture",      "Teinture",   "Teinture Jet",         "kg",    200, 0.48,  96, 2, "Thies",    "Moyenne"),
    ("M003", "Table de coupe automatique",   "Coupe",         "Decoupe",    "Coupe auto",           "piece", 300, 0.33, 100, 2, "Lectra",   "Moyenne"),
    ("M004", "Machine surjeteuse",           "Finition",      "Surjet",     "Surjet finition",      "piece", 400, 0.25, 100, 1, "Juki",     "Faible"),
    ("M005", "Presse vapeur industrielle",   "Finition",      "Repassage",  "Repassage industriel", "piece", 350, 0.30, 105, 1, "Veit",     "Moyenne"),
    ("M006", "Machine a broder 12 tetes",    "Broderie",      "Broderie",   "Broderie multi-tete",  "piece", 250, 0.36,  90, 2, "Tajima",   "Moyenne"),
    ("M007", "Metier a tricoter rectiligne", "Tissage",       "Tricotage",  "Tricot rectiligne",    "piece", 180, 0.55, 100, 2, "Stoll",    "Moyenne"),
    ("M008", "Machine d'impression textile", "Teinture",      "Impression", "Impression numerique", "metre", 600, 0.13,  76, 2, "Kornit",   "Elevee"),
    ("M009", "Plieuse emballage auto",       "Emballage",     "Emballage",  "Pliage et emballage",  "piece", 800, 0.08,  60, 1, "Svegea",   "Faible"),
    ("M010", "Controleuse tissu optique",    "Qualite",       "Controle",   "Controle optique",     "metre", 700, 0.09,  63, 1, "Uster",    "Faible"),
]

PRODUCTS = ["Tissu Denim", "Tissu Coton", "Tissu Polyester", "Fil Soie", "Broderie Luxe",
            "T-shirt Standard", "Chemise Premium", "Pantalon Classique", "Drap Housse", "Serviette Eponge"]

TASK_NAMES = [
    "Tissage lot", "Teinture batch", "Decoupe patron", "Surjet finition",
    "Repassage pieces", "Broderie motif", "Tricotage maille", "Impression motif",
    "Emballage lot", "Controle qualite"
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def rand_date(start_year=2015, end_year=2023):
    d = datetime(start_year, 1, 1) + timedelta(days=random.randint(0, (end_year - start_year) * 365))
    return d.strftime("%Y-%m-%d")

def rand_birth():
    age = random.randint(22, 58)
    year = 2026 - age
    d = datetime(year, random.randint(1, 12), random.randint(1, 28))
    return d.strftime("%Y-%m-%d"), age

# ---------------------------------------------------------------------------
# Generate employees
# ---------------------------------------------------------------------------
def gen_employees():
    emps = []
    for i in range(1, 501):
        eid = f"E{i:03d}"
        sexe = random.choice(SEXES)
        prenom = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
        nom = random.choice(NOMS)
        dob, age = rand_birth()
        shift = SHIFTS[i % 3]
        statut = random.choices(STATUT_PRESENCE, weights=[75, 15, 10])[0]
        anciennete = random.randint(1, 20)

        emps.append(employee(
            employee_id=eid,
            nom=nom,
            prenom=prenom,
            sexe=sexe,
            date_naissance=dob,
            age=age,
            etat_civil=random.choice(ETAT_CIVIL),
            nombre_enfants=random.randint(0, 5),
            niveau_etude=random.choice(NIVEAUX_ETUDE),
            poste=random.choice(POSTES),
            departement=random.choice(DEPARTEMENTS),
            type_contrat=random.choices(TYPES_CONTRAT, weights=[60, 25, 15])[0],
            anciennete_annees=anciennete,
            salaire_mensuel=random.randint(800, 2500),
            prime_rendement=random.randint(0, 400),
            heures_travail_semaine=random.choice([35, 40, 44, 48]),
            heures_absence_mois=random.randint(0, 16),
            retards_mois=random.randint(0, 8),
            jours_conge_restant=random.randint(0, 30),
            statut_presence=statut,
            rfid_uid=f"RFID-{eid}",
            shift_travail=shift,
            performance_moyenne=round(random.uniform(55, 98), 2),
            taux_rendement=round(random.uniform(0.6, 1.05), 4),
            accidents_travail=random.randint(0, 3),
            maladies_professionnelles=random.randint(0, 2),
            evaluation_manager=random.randint(1, 10),
            risque_absenteisme=random.choice(RISQUES),
            risque_depart=random.choice(RISQUES),
            date_embauche=rand_date(2026 - anciennete, 2026 - anciennete + 1),
        ))
    return emps

# ---------------------------------------------------------------------------
# Generate machines
# ---------------------------------------------------------------------------
def gen_machines():
    machines = []
    for mid, nom, atelier, tache, type_m, unite, cap, tpu, ttt, ops, marque, energie in MACHINE_DEFS:
        pannes = random.randint(0, 5)
        etat = "En panne" if pannes >= 4 else random.choices(["En marche", "Arretee", "En maintenance"], weights=[70, 15, 15])[0]
        machines.append(Machine(
            machine_id=mid,
            nom_machine=nom,
            type_machine=type_m,
            atelier=atelier,
            tache=tache,
            unite_production=unite,
            capacite=cap,
            temps_par_unite_min=tpu,
            temps_total_tache_min=ttt,
            operateurs_requis=ops,
            pannes_mois=pannes,
            etat_machine=etat,
            annee_installation=random.randint(2010, 2023),
            marque=marque,
            consommation_energie=energie,
            rendement_machine=round(random.uniform(0.70, 0.98), 4),
        ))
    return machines

# ---------------------------------------------------------------------------
# Machine mean durations (from model_meta.json)
# ---------------------------------------------------------------------------
MACHINE_MEANS = {
    "M001": 287.7, "M002": 95.7, "M003": 99.4, "M004": 98.5, "M005": 106.9,
    "M006": 89.7,  "M007": 97.9, "M008": 75.0, "M009": 60.5, "M010": 63.2,
}
MACHINE_STDS = {
    "M001": 64.7, "M002": 24.6, "M003": 26.0, "M004": 25.2, "M005": 26.2,
    "M006": 22.9, "M007": 25.5, "M008": 19.6, "M009": 16.5, "M010": 17.3,
}

# ---------------------------------------------------------------------------
# Generate production logs (last 60 days, ~5000 logs)
# ---------------------------------------------------------------------------
def gen_logs():
    logs = []
    now = datetime(2026, 3, 1, 6, 0, 0)
    start = now - timedelta(days=60)
    machine_ids = [f"M{i:03d}" for i in range(1, 11)]
    emp_ids = [f"E{i:03d}" for i in range(1, 501)]

    for day_offset in range(60):
        day = start + timedelta(days=day_offset)
        for shift_name, shift_start_h in [("Matin", 6), ("Jour", 14), ("Nuit", 22)]:
            n_tasks = random.randint(25, 35)
            for _ in range(n_tasks):
                mid = random.choice(machine_ids)
                eid = random.choice(emp_ids)
                mean_dur = MACHINE_MEANS[mid]
                std_dur = MACHINE_STDS[mid]
                duration = max(5.0, round(random.gauss(mean_dur, std_dur), 2))

                is_anomaly = 1 if random.random() < 0.06 else 0
                if is_anomaly:
                    duration = round(duration * random.uniform(1.8, 3.5), 2)

                task_status = "Interrompue" if (is_anomaly and random.random() < 0.4) else "Completee"
                hour = shift_start_h + random.randint(0, 7)
                minute = random.randint(0, 59)
                event_start = day.replace(hour=hour % 24, minute=minute)
                event_end = event_start + timedelta(minutes=duration)

                task_idx = machine_ids.index(mid)
                logs.append(FactoryLog(
                    log_id=f"L-{uuid.uuid4().hex[:12]}",
                    employee_id=eid,
                    machine_id=mid,
                    task_name=TASK_NAMES[task_idx],
                    tag_event_start=event_start.isoformat(),
                    tag_event_end=event_end.isoformat(),
                    task_duration_min=duration,
                    shift=shift_name,
                    product=random.choice(PRODUCTS),
                    task_status=task_status,
                    anomaly_flag=is_anomaly,
                ))
    return logs

# ---------------------------------------------------------------------------
# Generate alerts from anomalous logs
# ---------------------------------------------------------------------------
def gen_alerts(logs):
    alerts = []
    for log in logs:
        if log.anomaly_flag == 1:
            confidence = round(random.uniform(0.65, 0.99), 4)
            alerts.append(Alert(
                log_id=log.log_id,
                employee_id=log.employee_id,
                machine_id=log.machine_id,
                task_name=log.task_name,
                shift=log.shift,
                date_detection=log.tag_event_end or datetime.now().isoformat(),
                is_anomaly=1,
                confidence=confidence,
                score_raw=round(-confidence * random.uniform(0.3, 0.7), 4),
                label="Anomalie",
                task_duration_min=log.task_duration_min,
                task_status=log.task_status,
                anomaly_flag_original=1,
                statut=random.choices(["Nouvelle", "Vue", "Traitee"], weights=[40, 35, 25])[0],
            ))
    return alerts

# ---------------------------------------------------------------------------
# Generate monthly summaries (last 6 months)
# ---------------------------------------------------------------------------
def gen_monthly_summaries():
    summaries = []
    for m_offset in range(6, 0, -1):
        month = datetime(2026, 3, 1) - timedelta(days=30 * m_offset)
        periode = month.strftime("%Y-%m")
        total_tasks = random.randint(2500, 3200)
        completees = int(total_tasks * random.uniform(0.85, 0.95))
        anomalies = int(total_tasks * random.uniform(0.04, 0.08))
        total_emp = 500
        en_travail = random.randint(350, 420)
        absents = random.randint(30, 60)
        en_conge = total_emp - en_travail - absents

        summaries.append(MonthlySummary(
            periode=periode,
            date_generation=datetime.now().isoformat(),
            rendement_global_pct=round(random.uniform(78, 94), 2),
            duree_moyenne_taches_min=round(random.uniform(85, 130), 2),
            taux_anomalie_pct=round(anomalies / total_tasks * 100, 2),
            total_taches=total_tasks,
            taches_completees=completees,
            taches_interrompues=total_tasks - completees,
            total_anomalies=anomalies,
            total_employes=total_emp,
            employes_en_travail=en_travail,
            employes_absents=absents,
            employes_en_conge=en_conge,
            total_machines=10,
            machines_en_panne=random.randint(0, 2),
            rendement_matin=round(random.uniform(80, 95), 2),
            rendement_jour=round(random.uniform(78, 93), 2),
            rendement_nuit=round(random.uniform(70, 88), 2),
            score_fatigue_global=round(random.uniform(30, 65), 2),
            niveau_fatigue_global=random.choice(["Faible", "Moyen", "Eleve"]),
            employes_fatigue_critique=random.randint(5, 25),
            employes_fatigue_eleve=random.randint(30, 70),
            employes_fatigue_moyen=random.randint(100, 200),
            employes_fatigue_faible=random.randint(200, 350),
        ))
    return summaries

# ---------------------------------------------------------------------------
# Generate shift summaries (last 10 days)
# ---------------------------------------------------------------------------
def gen_shift_summaries():
    summaries = []
    for d_offset in range(10, 0, -1):
        day = datetime(2026, 3, 1) - timedelta(days=d_offset)
        date_str = day.strftime("%Y-%m-%d")
        for shift in SHIFTS:
            total = random.randint(80, 120)
            completees = int(total * random.uniform(0.85, 0.95))
            anomalies = int(total * random.uniform(0.03, 0.08))
            summaries.append(ShiftSummary(
                date=date_str,
                shift=shift,
                date_generation=datetime.now().isoformat(),
                rendement_pct=round(random.uniform(75, 96), 2),
                duree_moyenne_min=round(random.uniform(80, 140), 2),
                taux_anomalie_pct=round(anomalies / total * 100, 2),
                total_taches=total,
                taches_completees=completees,
                taches_interrompues=total - completees,
                total_anomalies=anomalies,
                total_employes_shift=random.randint(130, 180),
                score_fatigue_shift=round(random.uniform(25, 70), 2),
                niveau_fatigue_shift=random.choice(["Faible", "Moyen", "Eleve"]),
                employes_fatigue_critique=random.randint(2, 10),
                employes_fatigue_eleve=random.randint(10, 30),
                employes_fatigue_moyen=random.randint(30, 60),
                employes_fatigue_faible=random.randint(60, 100),
            ))
    return summaries

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Initializing database (creating tables)...")
    init_db()

    print("Generating seed data...")
    employees = gen_employees()
    machines = gen_machines()
    logs = gen_logs()
    alerts = gen_alerts(logs)
    monthly = gen_monthly_summaries()
    shifts = gen_shift_summaries()

    print(f"  Employees:        {len(employees)}")
    print(f"  Machines:         {len(machines)}")
    print(f"  Production logs:  {len(logs)}")
    print(f"  Alerts:           {len(alerts)}")
    print(f"  Monthly summaries:{len(monthly)}")
    print(f"  Shift summaries:  {len(shifts)}")

    with Session(engine) as session:
        print("\nInserting employees...")
        for e in employees:
            session.add(e)
        session.commit()

        print("Inserting machines...")
        for m in machines:
            session.add(m)
        session.commit()

        print("Inserting production logs (this may take a moment)...")
        for batch_start in range(0, len(logs), 500):
            batch = logs[batch_start:batch_start + 500]
            for log in batch:
                session.add(log)
            session.commit()
            print(f"  ...{min(batch_start + 500, len(logs))}/{len(logs)} logs")

        print("Inserting alerts...")
        for a in alerts:
            session.add(a)
        session.commit()

        print("Inserting monthly summaries...")
        for ms in monthly:
            session.add(ms)
        session.commit()

        print("Inserting shift summaries...")
        for ss in shifts:
            session.add(ss)
        session.commit()

    print("\nSeed complete!")

if __name__ == "__main__":
    main()
