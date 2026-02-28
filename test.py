@router.post("/rfid")
def save_production(payload: UIDModel, session: Session = Depends(get_session)):
    print(payload)
    try:
        # Chercher l'employé par code RFID
        employee = session.exec(select(Employee).where(Employee.identifiant_ui == payload.uid)).first()
        print(employee)
        if not employee:
            return {"status": 400, "data": []}
        machine=session.exec(select(Machine).where(Machine.id==payload.machine_id)).first()
        print(machine)
        # Chercher la tâche associée à la machine
        task = session.exec(select(Task).where(Task.machine_utilisee == machine.nom)).first()
        print(task)
        if not task:
            return {"status": 400, "data": []}
        
        # Chercher session en cours pour cet employé et tâche
        log = session.exec(
            select(production_logs)
            .where(production_logs.employe_id == employee.id)
            .where(production_logs.tache_id == task.id)
            .where(production_logs.fin_tache == None)
        ).first()

        if log:
            # Fin de session : calcul rendement et mise à jour
            log.fin_tache = payload.timestamp
            duration_sec = (log.fin_tache - log.debut_tache).total_seconds()
            log.pieces_produites = task.pieces_par_tache
            log.sets_produits = task.pieces_par_tache // task.pieces_par_set
            log.rendement_pct = (task.pieces_par_tache / duration_sec) * 100  # simple estimation 
            session.add(log)
            session.commit()
            session.refresh(log)
            return {"status": 200, "data": log}
        else:
            # Début d'une nouvelle session
            new_log = production_logs(
                employe_id=employee.id,
                tache_id=task.id,
                debut_tache=payload.timestamp,
                fin_tache=None,
                pieces_produites=0,
                sets_produits=0,
                rendement_pct=0
            )
            session.add(new_log)
            session.commit()
            session.refresh(new_log)
            return {"status": 200, "data": new_log}

    except Exception as e:
        print(e)
        session.rollback()
        return {"status": 400, "data": []}