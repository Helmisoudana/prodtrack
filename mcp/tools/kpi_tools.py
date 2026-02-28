import httpx
from server import mcp

BASE_URL = "http://localhost:8000"


@mcp.tool()
async def get_kpi_rendement_global() -> dict:
    """Get KPI global rendement metrics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/kpis/rendement-global")
        return response.json()


@mcp.tool()
async def get_kpi_rendement_par_employe(employee_id: str | None = None) -> dict:
    """Get KPI rendement per employee. Optionally filter by employee_id."""
    params = {"employee_id": employee_id} if employee_id else None
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/kpis/rendement-par-employe",
            params=params,
        )
        return response.json()


@mcp.tool()
async def get_kpi_duree_moyenne_taches() -> dict:
    """Get KPI average task duration metrics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/kpis/duree-moyenne-taches")
        return response.json()


@mcp.tool()
async def get_kpi_summary() -> dict:
    """Get KPI global summary dashboard metrics."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/kpis/summary")
        return response.json()
