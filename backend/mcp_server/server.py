from backend.mcp_server import mcp

# Importing these modules ensures the decorators are executed and tools are registered
from backend.mcp_server.tools import planner_tools
from backend.mcp_server.tools import insight_tools
from backend.mcp_server.tools import template_tools
from backend.mcp_server import resources

# Optional: You can add an __all__ or just expose mcp
__all__ = ["mcp"]
