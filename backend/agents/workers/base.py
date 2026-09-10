import abc
import json
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from backend.mcp_server.server import mcp
from backend.services.llm_client import BaseLLMClient

logger = logging.getLogger(__name__)

class BaseWorker(abc.ABC):
    """Baseworker."""
    def __init__(self, llm_client: BaseLLMClient):
        """  init  ."""
        self.llm_client = llm_client
        self.allowed_tools = []

    @abc.abstractmethod
    async def process(self, user_id: UUID, message: str, context: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process the user message according to the worker's specialty."""
        pass

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool."""
        if tool_name not in self.allowed_tools:
            return {"error": f"Tool {tool_name} is not allowed for this worker."}
        
        try:
            logger.info(f"Executing tool {tool_name} with args {arguments}")
            result = await mcp.call_tool(tool_name, arguments)
            if hasattr(result, "is_error") and result.is_error:
                return {"error": result.content}
                
            if hasattr(result, "structured_content"):
                return result.structured_content
                
            return {"result": result.content}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}

    async def get_tool_schemas(self) -> str:
        """Returns a compact text description of allowed tools for LLM prompts.
        
        Uses a concise format instead of full JSON Schema to keep prompt size
        small enough for 7B models.
        """
        lines = []
        for tool_name in self.allowed_tools:
            tool_obj = await mcp.get_tool(tool_name)
            if tool_obj:
                # Extract just parameter names and types from the schema
                params = tool_obj.parameters or {}
                properties = params.get("properties", {})
                required = params.get("required", [])
                
                param_parts = []
                for pname, pschema in properties.items():
                    ptype = pschema.get("type", "string")
                    req_marker = "*" if pname in required else "?"
                    param_parts.append(f"{pname}:{ptype}{req_marker}")
                
                params_str = ", ".join(param_parts)
                lines.append(f"- {tool_obj.name}({params_str}): {tool_obj.description}")
        
        return "\n".join(lines)
