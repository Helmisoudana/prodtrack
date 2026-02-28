import httpx
from server import mcp

# mcp/tools/employeeTools.py

import httpx
from server import mcp

BASE_URL = "http://localhost:8000"  # ← change to your FastAPI port

@mcp.tool()
async def get_employees(page: int = 1, limit: int = 20) -> dict:
    """Get paginated list of employees from the database."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/employees",
            params={"page": page, "limit": limit}
        )
        return response.json()