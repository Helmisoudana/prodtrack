# routes/task.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from models.taches import Task
from database.session import get_session

router = APIRouter(prefix="/tache", tags=["tache"])

# -------------------------------
# Liste tâches
# GET /tasks
# -------------------------------
@router.get("/")
def get_tasks(session: Session = Depends(get_session)):
    try:
        tasks = session.exec(select(Task)).all()
        return {"status": 200, "data": tasks}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Détail tâche
# GET /tasks/{task_id}
# -------------------------------
@router.get("/{task_id}")
def get_task(task_id: int, session: Session = Depends(get_session)):
    try:
        task = session.get(Task, task_id)
        if not task:
            return {"status": 400, "data": []}
        return {"status": 200, "data": task}
    except Exception as e:
        return {"status": 400, "data": []}

# -------------------------------
# Créer tâche
# POST /tasks
# -------------------------------
@router.post("/")
def create_task(task: Task, session: Session = Depends(get_session)):
    try:
        session.add(task)
        session.commit()
        session.refresh(task)
        return {"status": 200, "data": task}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier tâche
# PUT /tasks/{task_id}
# -------------------------------
@router.put("/{task_id}")
def update_task(task_id: int, task_data: Task, session: Session = Depends(get_session)):
    try:
        task = session.get(Task, task_id)
        if not task:
            return {"status": 400, "data": []}
        task.nom_tache = task_data.nom_tache
        task.temps_tache_sec = task_data.temps_tache_sec
        task.pieces_par_tache = task_data.pieces_par_tache
        task.pieces_par_set = task_data.pieces_par_set
        task.temps_finir_set = task_data.temps_finir_set
        task.machine_utilisee = task_data.machine_utilisee
        task.difficulte = task_data.difficulte
        session.add(task)
        session.commit()
        session.refresh(task)
        return {"status": 200, "data": task}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer tâche
# DELETE /tasks/{task_id}
# -------------------------------
@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    try:
        task = session.get(Task, task_id)
        if not task:
            return {"status": 400, "data": []}
        session.delete(task)
        session.commit()
        return {"status": 200, "data": {"message": "Task deleted successfully"}}
    except Exception as e:
        session.rollback()
        return {"status": 400, "data": []}
