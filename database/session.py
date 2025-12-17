from sqlmodel import Session, create_engine, SQLModel
from dotenv import load_dotenv
from contextlib import contextmanager
import os

load_dotenv()

DATABASE_URL = os.getenv("MYSQL_URL")
engine = create_engine(DATABASE_URL, echo=True)
def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    from models.employee import Employee
    from models.machine import Machine
    from models.taches import Task
    from models.shift import Shift
    from models.rfid_tag import RFIDTag
    from models.presence import Presence
    from models.machine_session import MachineSession
    from models.production_log import production_logs
    from models.assignment import Assignment
    # Importer autres models si nécessaire

    SQLModel.metadata.create_all(engine)