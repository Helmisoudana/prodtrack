# ml/anomaly_service.py
import joblib
import json
import numpy as np
import os

BASE_DIR = os.path.dirname(__file__)

iso_model = joblib.load(os.path.join(BASE_DIR, 'isolation_forest.pkl'))

with open(os.path.join(BASE_DIR, 'model_meta.json'), 'r') as f:
    meta = json.load(f)

FEATURES      = meta['features']
EMP_STATS     = {e['employee_id']: e for e in meta['emp_stats']}
MACHINE_STATS = {m['machine_id']: m for m in meta['machine_stats']}

# ── Encodages identiques au notebook ────────────────────────────────
SHIFT_ENC   = {'Matin': 0, 'Jour': 1, 'ApresMidi': 2, 'Nuit': 3}
STATUS_ENC  = {'Completee': 0, 'Interrompue': 1}
PRODUCT_ENC = {}  # sera rempli depuis model_meta.json

def parse_float(val) -> float:
    if val is None: return 0.0
    try:    return float(str(val).replace(",", "."))
    except: return 0.0

def build_features(log, machine, emp) -> list:

    task_duration_min = parse_float(log.task_duration_min)

    # ── 5B. Durée ────────────────────────────────────────────────────
    std_duration      = parse_float(machine.temps_par_unite_min) if machine else 1.0
    duration_ratio    = task_duration_min / (std_duration + 1e-8)
    duration_deviation = task_duration_min - std_duration
    duration_abs_dev  = abs(duration_deviation)

    m_stats         = MACHINE_STATS.get(log.machine_id, {})
    machine_mean    = m_stats.get('machine_mean', std_duration)
    machine_std     = float(m_stats.get('machine_std') or 1.0)
    machine_z_score = (task_duration_min - machine_mean) / (machine_std + 1e-8)

    # ── 5C. Profil employé ───────────────────────────────────────────
    e_stats        = EMP_STATS.get(log.employee_id, {})
    emp_mean_ratio = float(e_stats.get('emp_mean_ratio') or 1.0)
    emp_std_ratio  = float(e_stats.get('emp_std_ratio')  or 0.1)
    emp_task_count = float(e_stats.get('emp_task_count') or 1)
    emp_deviation  = duration_ratio - emp_mean_ratio

    # ── Machine meta ─────────────────────────────────────────────────
    machine_rendement = parse_float(machine.rendement_machine) if machine else 0.9
    machine_pannes    = int(machine.pannes_mois or 0)          if machine else 0
    machine_age       = int(2025 - (machine.annee_installation or 2020)) if machine else 5

    # ── Encodages catégorielles ──────────────────────────────────────
    product_enc = meta.get('product_enc', {}).get(log.product or '', 0)
    status_enc  = STATUS_ENC.get(log.task_status or '', 0)

    # ── Map features dans l'ordre exact du notebook ──────────────────
    features_map = {
        'task_duration_min':  task_duration_min,
        'duration_ratio':     duration_ratio,
        'duration_deviation': duration_deviation,
        'duration_abs_dev':   duration_abs_dev,
        'machine_z_score':    machine_z_score,
        'emp_deviation':      emp_deviation,
        'machine_rendement':  machine_rendement,
        'machine_pannes':     machine_pannes,
        'machine_age':        machine_age,
        'product_enc':        product_enc,
        'status_enc':         status_enc,
        'emp_std_ratio':      emp_std_ratio,
        'emp_task_count':     emp_task_count,
    }

    return [features_map.get(f, 0.0) for f in FEATURES]

def predict_anomaly(log, machine, emp) -> dict:
    try:
        features   = build_features(log, machine, emp)
        X          = np.array(features).reshape(1, -1)
        prediction = iso_model.predict(X)[0]
        score      = iso_model.score_samples(X)[0]
        is_anomaly = int(prediction == -1)
        confidence = round(float(np.clip(-score, 0, 1)), 3)

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "score_raw":  round(float(score), 4),
            "label":      "Anomalie" if is_anomaly else "Normal"
        }
    except Exception as e:
        return {
            "is_anomaly": 0, "confidence": 0.0,
            "score_raw":  0.0, "label": "Erreur", "error": str(e)
        }