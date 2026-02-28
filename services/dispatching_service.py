import os
import mysql.connector
import random
import numpy as np
from scipy.optimize import linear_sum_assignment
from dotenv import load_dotenv
load_dotenv()  # Charge les variables d'environnement depuis le fichier .env





def run_dispatching_hungarian():
    # -----------------------
    # CONNECT TO MYSQL
    # -----------------------
    conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB")
    )
    cursor = conn.cursor(dictionary=True)

    # -----------------------
    # GET AVERAGE TIMES PER (machine, product, employee)
    # -----------------------
    cursor.execute("""
    SELECT machine_id, product, employee_id,
           AVG(task_duration_min) AS avg_time
    FROM factory_logs
    WHERE anomaly_flag = 0
    GROUP BY machine_id, product, employee_id;
    """)
    results = cursor.fetchall()

    # fitness_dict[machine_id][product][employee_id] = avg_time
    fitness_dict = {}
    machine_employees = {}  # machine_id -> set of employees

    for row in results:
        machine = row["machine_id"]
        product = row["product"]
        emp = row["employee_id"]
        avg_time = float(row["avg_time"])

        if machine not in fitness_dict:
            fitness_dict[machine] = {}
        if product not in fitness_dict[machine]:
            fitness_dict[machine][product] = {}
        fitness_dict[machine][product][emp] = avg_time

        if machine not in machine_employees:
            machine_employees[machine] = set()
        machine_employees[machine].add(emp)

    cursor.close()
    conn.close()

    # -----------------------
    # RUN HUNGARIAN PER MACHINE
    # -----------------------
    PENALTY = 999999  # cost for employee with no data for a product

    all_assignments = []
    all_unassigned = []
    total_time = 0.0

    machines = sorted(fitness_dict.keys())

    for machine in machines:
        products = sorted(fitness_dict[machine].keys())  # 5 products
        employees = sorted(machine_employees[machine])   # ~50 employees

        num_products = len(products)    # 5
        num_employees = len(employees)  # ~50

        # Build cost matrix: rows = employees, cols = products
        cost_matrix = np.full((num_employees, num_products), PENALTY, dtype=float)

        for i, emp in enumerate(employees):
            for j, product in enumerate(products):
                if emp in fitness_dict[machine].get(product, {}):
                    cost_matrix[i][j] = fitness_dict[machine][product][emp]

        # Transpose: (num_products x num_employees)
        # Assigns each product to its optimal employee
        row_ind, col_ind = linear_sum_assignment(cost_matrix.T)

        assigned_employees = set()

        for product_idx, emp_idx in zip(row_ind, col_ind):
            emp = employees[emp_idx]
            product = products[product_idx]
            time = cost_matrix[emp_idx][product_idx]

            if time >= PENALTY:
                all_unassigned.append({
                    "employee_id": emp,
                    "machine_id": machine,
                    "reason": f"No data for {product}"
                })
                continue

            all_assignments.append({
                "employee_id": emp,
                "machine_id": machine,
                "product": product,
                "avg_time_min": round(time, 2)
            })
            assigned_employees.add(emp)
            total_time += time

        

    # -----------------------
    # BUILD SUMMARY
    # -----------------------
    machine_summary = {}
    for a in all_assignments:
        m = a["machine_id"]
        if m not in machine_summary:
            machine_summary[m] = {"assigned": 0, "total_time_min": 0.0, "tasks": []}
        machine_summary[m]["assigned"] += 1
        machine_summary[m]["total_time_min"] += a["avg_time_min"]
        machine_summary[m]["tasks"].append(
            f"{a['employee_id']} -> {a['product']} ({a['avg_time_min']} min)"
        )

    return {
        "algorithm": "Hungarian (linear_sum_assignment)",
        "priority": "Minimize total time",
        "diagnostics": {
            "assigned_employees": len(all_assignments),
            "total_time_min": round(total_time, 2)
        },
        "assignments": all_assignments,
    }

def worst_real_dispatching(day: str):
    """
    Retourne le pire employé par machine/product pour une date donnée
    day format: YYYY-MM-DD
    """
    conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB")
    )
    cursor = conn.cursor(dictionary=True)

    query = f"""
    WITH avg_times AS (
        SELECT 
            machine_id,
            product,
            employee_id,
            ROUND(AVG(task_duration_min),2) AS avg_time
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
    ORDER BY machine_id, product;
    """

    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results