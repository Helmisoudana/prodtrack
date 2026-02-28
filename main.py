from fastapi import FastAPI
from database.session import init_db
import uvicorn
from fastapi.middleware.cors import CORSMiddleware




from routers import (
    employee,
    machine,
    production_log,
    kpis,
    llm,
    dispatching

    # tache,          # pas encore converti
    # shift,          # pas encore converti
    # rfid_tag,       # pas encore converti
    # presence,       # pas encore converti
    # machine_session,# pas encore converti
    # assignment,     # pas encore converti
)

app = FastAPI(title="Usine Smart Factory", redirect_slashes=False)

init_db()
app.include_router(kpis.router)
app.include_router(employee.router)
app.include_router(machine.router)
app.include_router(production_log.router)
app.include_router(llm.router)
app.include_router(dispatching.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)