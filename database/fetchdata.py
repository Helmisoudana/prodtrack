from sqlmodel import SQLModel, create_engine, Session, select ,desc
from database.session import get_session
from models.employee import emplyees
from models.production_logs import production_logs
from models.taches import taches
from datetime import datetime


def getemployee(payload):
    with get_session() as session:   # ici ça MARCHE car get_session est un contextmanager
        statement = select(emplyees).where(emplyees.identifiant_ui == payload.uid)
        result = session.exec(statement).first()
        return result



def getproductionbyemployee(id):
    with get_session() as session:   # ici ça MARCHE car get_session est un contextmanager
        statement = select(production_logs).where(production_logs.employe_id == id).order_by(desc(production_logs.id))
        result = session.exec(statement).first()
        return result
    



def update_date_fin(log_id, temps, nbpieces, nbsets):
    with get_session() as session:
        # Chercher la ligne à modifier
        statement = select(production_logs).where(production_logs.id == log_id)
        log = session.exec(statement).first()

        if log:
            # Date/heure de fin = maintenant
            log.fin_tache = datetime.now()

            # Différence en secondes entre début et fin
            diff_sec = (log.fin_tache - log.debut_tache).total_seconds()

            # Calcul du rendement en pourcentage
            log.rendement_pct = ( temps / diff_sec) * 100

            # Mise à jour des autres champs
            log.pieces_produites = nbpieces
            log.sets_produits = nbsets

            # Sauvegarder en base
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        else:
            return None

        


def gettachebyid(payload):
    with get_session() as session:   # ici ça MARCHE car get_session est un contextmanager
        statement = select(taches).where(taches.id == payload.idtache)
        result = session.exec(statement).first()
        return result


def ajouter_production(employee_id: int, tache_id: int):
    with get_session() as session:
        # Créer un nouvel enregistrement
        new_log = production_logs(
            employe_id=employee_id,
            tache_id=tache_id,
            debut_tache=datetime.now(),   # date/heure actuelle
            fin_tache=None,               # pas encore terminée
            rendement_pct=0,              # initialisé à 0
            pieces_produites=0,           # pas encore de production
            sets_produits=0               # idem
        )

        # Ajouter dans la base
        session.add(new_log)
        session.commit()
        session.refresh(new_log)

        return new_log

    