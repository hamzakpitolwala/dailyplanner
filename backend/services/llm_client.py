import abc
import json
import logging
import httpx
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class BaseLLMClient(abc.ABC):
    @abc.abstractmethod
    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        pass


class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str = "http://localhost:11434/api/chat", model: str = "llama3.1"):
        self.base_url = base_url
        self.model = model

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                resp = await client.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
            except httpx.HTTPError as e:
                logger.error(f"LLM Client HTTP Error: {e}")
                raise HTTPException(status_code=502, detail="Failed to communicate with LLM provider.")


class LLMResponseValidator:
    def __init__(self, client: BaseLLMClient):
        self.client = client

    async def generate_and_parse(self, system_prompt: str, user_prompt: str, model_cls: Type[T]) -> T:
        """Generates response and attempts to parse it into the given Pydantic model with 1 retry."""
        content = await self.client.chat(system_prompt, user_prompt)
        
        try:
            return self._parse(content, model_cls)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse LLM response on first attempt: {e}. Retrying...")
            
            # Retry once with a stronger reminder
            retry_prompt = user_prompt + "\n\nWARNING: Your previous response did not match the schema. Output ONLY valid JSON as per schema, no extra text, no markdown blocks."
            content_retry = await self.client.chat(system_prompt, retry_prompt)
            try:
                return self._parse(content_retry, model_cls)
            except (json.JSONDecodeError, ValidationError) as e2:
                logger.error(f"Failed to parse LLM response on second attempt: {e2}")
                raise HTTPException(status_code=502, detail="AI response format invalid")

    def _parse(self, content: str, model_cls: Type[T]) -> T:
        # Sometimes LLMs wrap JSON in markdown blocks like ```json ... ```
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        raw = json.loads(content)
        return model_cls.model_validate(raw)
