import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, ValidationError

# For LLM generation, assume there's a function we can use or we mock it
# In Phase 8, the prompt mentions using Ollama for LLM generation
import httpx

from backend.db.models.ai_engine import AIRecommendation
from backend.services.pattern_scanner import PatternEvent

logger = logging.getLogger(__name__)

class LLMRecommendationResponse(BaseModel):
    kind: str
    scope: str
    target: Dict[str, Optional[str]]
    payload: Dict[str, Any]
    title: str
    explanation: str
    confidence: float

class RecommendationAgent:
    """Agent that interacts with LLM to generate recommendations and make execution decisions."""
    
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM API."""
        logger.info(f"Calling LLM {self.model_name}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "[]")
        except Exception as e:
            logger.error(f"Failed to communicate with LLM: {e}")
            return "[]"

    async def generate_recommendations(self, user_profile: dict, history: dict, patterns: List[PatternEvent]) -> List[LLMRecommendationResponse]:
        """Generate recommendations based on patterns."""
        system_prompt = (
            "You are an assistant that analyzes a user's daily planner data and suggests small, concrete schedule improvements.\n"
            "Respond ONLY with a JSON array of recommendations matching the required schema."
        )
        
        user_prompt = f"""
        User profile: {json.dumps(user_profile)}
        History: {json.dumps(history)}
        Detected Patterns: {json.dumps([p.to_dict() for p in patterns])}
        
        Please propose up to 3 specific changes that are realistic for next week.
        """
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = await self._call_llm(full_prompt)
        
        recs = []
        try:
            data = json.loads(response_text)
            if isinstance(data, list):
                for item in data:
                    try:
                        recs.append(LLMRecommendationResponse(**item))
                    except ValidationError as ve:
                        logger.warning(f"Invalid recommendation format from LLM: {ve}")
        except json.JSONDecodeError:
            logger.error("LLM did not return valid JSON")
            
        return recs


        return recs
