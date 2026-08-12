import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from backend.agents.recommendation_agent import RecommendationAgent

@pytest.mark.asyncio
async def test_generate_recommendations_success():
    agent = RecommendationAgent()
    
    # Mock httpx.AsyncClient.post
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": """
        [
            {
                "kind": "break_suggestion",
                "scope": "daily",
                "target": {},
                "payload": {"break_minutes": 15},
                "title": "Take a break",
                "explanation": "You've been working hard",
                "confidence": 0.8
            }
        ]
        """
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", new=mock_post):
        recommendations = await agent.generate_recommendations("dummy_context", [], [])
        assert len(recommendations) == 1
        assert recommendations[0].kind == "break_suggestion"
        assert recommendations[0].title == "Take a break"


@pytest.mark.asyncio
async def test_generate_recommendations_json_decode_error():
    agent = RecommendationAgent()
    
    # Mock httpx.AsyncClient.post to return invalid JSON text
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": "This is not valid JSON."
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", new=mock_post):
        recommendations = await agent.generate_recommendations("dummy_context", [], [])
        # Should gracefully return empty list on parsing failure
        assert len(recommendations) == 0


@pytest.mark.asyncio
async def test_generate_recommendations_httpx_error():
    agent = RecommendationAgent()
    
    # Mock httpx.AsyncClient.post to raise an HTTPError
    mock_post = AsyncMock(side_effect=httpx.HTTPError("Timeout"))

    with patch("httpx.AsyncClient.post", new=mock_post):
        recommendations = await agent.generate_recommendations("dummy_context", [], [])
        # Should gracefully return empty list
        assert len(recommendations) == 0
