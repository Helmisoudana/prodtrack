import httpx
from server import mcp

BASE_URL = "http://localhost:8000"


@mcp.tool()
async def get_dispatching_hungarian() -> dict:
    """Run dispatching with the Hungarian algorithm."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/dispatching/hungarian")
        return response.json()


@mcp.tool()
async def get_dispatching_worst_real(day: str) -> dict:
    """Get worst real dispatching for a given day (YYYY-MM-DD)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/dispatching/worst_real",
            params={"day": day},
        )
        return response.json()
