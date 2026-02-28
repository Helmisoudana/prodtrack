from sqlmodel import Session, create_engine, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("MYSQL_URL")
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    from models.employee import employee
    from models.machine import Machine
    from models.production_log import FactoryLog
    from models.monthly_summary import MonthlySummary 
    from models.shift_summary import ShiftSummary
    from models.alert import Alert
    # ajoute les autres models ici au fur et à mesure

    SQLModel.metadata.create_all(engine)