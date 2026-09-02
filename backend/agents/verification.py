import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VerificationLayer:
    def __init__(self):
        pass

    def verify_action(self, user_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify if an action is safe to execute.
        This checks basic constraints, tenant isolation, and confirmation requirements.
        """
        try:
            # If the action has no tool_name, it's just a conversation response
            if "tool_name" not in action_data:
                return {
                    "is_safe": True,
                    "requires_confirmation": False
                }
                
            tool_name = action_data["tool_name"]
            arguments = action_data.get("arguments", {})
            
            # Tenant isolation check: Ensure user_id matches if present in arguments
            if "user_id" in arguments and str(arguments["user_id"]) != str(user_id):
                return {
                    "is_safe": False,
                    "error": "Security violation: Attempted to modify data for another user."
                }
                
            # Check read-only vs mutation
            read_only_tools = [
                "get_tasks", "get_schedule", "get_today_summary", 
                "get_overdue_tasks", "find_schedule_conflicts", "get_analytics",
                "list_templates"
            ]
            
            if tool_name in read_only_tools:
                return {
                    "is_safe": True,
                    "requires_confirmation": False
                }
            
            # All other tools are mutations and require confirmation
            return {
                "is_safe": True,
                "requires_confirmation": True
            }
        except Exception as e:
            logger.error(f"Verification check failed: {e}")
            return {
                "is_safe": False,
                "error": str(e)
            }
