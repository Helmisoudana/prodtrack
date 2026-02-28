from server import mcp

from tools.employee_tools import get_employees
from tools.kpi_tools import (
    get_kpi_duree_moyenne_taches,
    get_kpi_rendement_global,
    get_kpi_rendement_par_employe,
    get_kpi_summary,
)
from tools.dispatching_tools import (
    get_dispatching_hungarian,
    get_dispatching_worst_real,
)

def main():
    print("MCP server started, waiting for requests...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()