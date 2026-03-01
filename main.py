from fastapi import FastAPI
from database.session import init_db
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from routers import alert

# database/session.py — ajouter dans init_db()

from routers import employee, machine, production_log, kpis, monthly_summary, shift_summary, anomaly, dispatching, llm
from scheduler.monthly_job import generate_monthly_summary
from scheduler.shift_job import generate_shift_summary

app = FastAPI(title="Usine Smart Factory", redirect_slashes=False)

init_db()

scheduler = BackgroundScheduler()

# Monthly: 1er du mois à minuit
scheduler.add_job(
    generate_monthly_summary,
    trigger=CronTrigger(day=1, hour=0, minute=0),
    id="monthly_summary",
    replace_existing=True
)

# Shift Matin: se termine à 14h → générer à 14h05
scheduler.add_job(
    generate_shift_summary,
    trigger=CronTrigger(hour=14, minute=5),
    args=["Matin"],
    id="shift_matin",
    replace_existing=True
)

# Shift Jour: se termine à 22h → générer à 22h05
scheduler.add_job(
    generate_shift_summary,
    trigger=CronTrigger(hour=22, minute=5),
    args=["Jour"],
    id="shift_jour",
    replace_existing=True
)

# Shift Nuit: se termine à 6h → générer à 6h05
scheduler.add_job(
    generate_shift_summary,
    trigger=CronTrigger(hour=6, minute=5),
    args=["Nuit"],
    id="shift_nuit",
    replace_existing=True
)

scheduler.start()

app.include_router(employee.router)
app.include_router(machine.router)
app.include_router(production_log.router)
app.include_router(kpis.router)
app.include_router(monthly_summary.router)
app.include_router(shift_summary.router)
app.include_router(alert.router)
app.include_router(anomaly.router)
app.include_router(dispatching.router)
app.include_router(llm.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)