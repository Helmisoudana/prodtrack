# services/dispatching_service.py
import numpy as np
from scipy.optimize import linear_sum_assignment
from sqlmodel import Session, select, text
from models.production_log import FactoryLog


PENALTY = 999999


def run_dispatching_hungarian(session: Session):
    # -----------------------
    # GET AVERAGE TIMES PER (machine, product, employee)
    # -----------------------
    results = session.exec(text("""
        SELECT machine_id, product, employee_id,
               AVG(task_duration_min) AS avg_time
        FROM factory_logs
        WHERE anomaly_flag = 0
        GROUP BY machine_id, product, employee_id
    """)).all()

    # fitness_dict[machine_id][product][employee_id] = avg_time
    fitness_dict = {}
    machine_employees = {}

    for row in results:
        machine  = row.machine_id
        product  = row.product
        emp      = row.employee_id
        avg_time = float(row.avg_time)

        if machine not in fitness_dict:
            fitness_dict[machine] = {}
        if product not in fitness_dict[machine]:
            fitness_dict[machine][product] = {}
        fitness_dict[machine][product][emp] = avg_time

        if machine not in machine_employees:
            machine_employees[machine] = set()
        machine_employees[machine].add(emp)

    # -----------------------
    # RUN HUNGARIAN PER MACHINE
    # -----------------------
    all_assignments = []
    all_unassigned  = []
    total_time      = 0.0

    for machine in sorted(fitness_dict.keys()):
        products  = sorted(fitness_dict[machine].keys())
        employees = sorted(machine_employees[machine])

        num_products  = len(products)
        num_employees = len(employees)

        cost_matrix = np.full((num_employees, num_products), PENALTY, dtype=float)

        for i, emp in enumerate(employees):
            for j, product in enumerate(products):
                if emp in fitness_dict[machine].get(product, {}):
                    cost_matrix[i][j] = fitness_dict[machine][product][emp]

        row_ind, col_ind = linear_sum_assignment(cost_matrix.T)

        for product_idx, emp_idx in zip(row_ind, col_ind):
            emp     = employees[emp_idx]
            product = products[product_idx]
            time    = cost_matrix[emp_idx][product_idx]

            if time >= PENALTY:
                all_unassigned.append({
                    "employee_id": emp,
                    "machine_id":  machine,
                    "reason":      f"No data for {product}"
                })
                continue

            all_assignments.append({
                "employee_id":  emp,
                "machine_id":   machine,
                "product":      product,
                "avg_time_min": round(time, 2)
            })
            total_time += time

    # -----------------------
    # BUILD SUMMARY
    # -----------------------
    return {
        "algorithm": "Hungarian (linear_sum_assignment)",
        "priority":  "Minimize total time",
        "diagnostics": {
            "assigned_employees": len(all_assignments),
            "total_time_min":     round(total_time, 2)
        },
        "assignments": all_assignments,
    }


def worst_real_dispatching(day: str, session: Session):
    """
    Retourne le pire employé par machine/product pour une date donnée.
    day format: YYYY-MM-DD
    """
    results = session.exec(text(f"""
        WITH avg_times AS (
            SELECT 
                machine_id,
                product,
                employee_id,
                ROUND(AVG(task_duration_min), 2) AS avg_time
            FROM factory_logs
            WHERE tag_event_start >= '{day} 00:00:00'
              AND tag_event_start <  '{day} 23:59:59'
              AND anomaly_flag = 0
            GROUP BY machine_id, product, employee_id
        )
        SELECT machine_id,
               product,
               employee_id,
               avg_time
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY machine_id, product
                       ORDER BY avg_time DESC
                   ) AS rn
            FROM avg_times
        ) ranked
        WHERE rn = 1
        ORDER BY machine_id, product
    """)).all()

    return [
        {
            "machine_id":  row.machine_id,
            "product":     row.product,
            "employee_id": row.employee_id,
            "avg_time":    row.avg_time
        }
        for row in results
    ]