from fastapi import FastAPI
from database.session import init_db
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    employee,
    machine,
    tache,
    shift,
    rfid_tag,
    presence,
    machine_session,
    production_log,
    assignment,
    #recommendation  # si tu ajoutes IA
)

app = FastAPI(title="Usine Smart Factory")

# Initialisation DB
init_db()

# Inclure les routers
app.include_router(employee.router)
app.include_router(machine.router)
app.include_router(tache.router)
app.include_router(shift.router)
app.include_router(rfid_tag.router)
app.include_router(presence.router)
app.include_router(machine_session.router)
app.include_router(production_log.router)
#app.include_router(assignment.router)
#app.include_router(recommendation.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod → domaine frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

