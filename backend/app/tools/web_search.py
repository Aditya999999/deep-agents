"""
ForgeX — Web Search Tool

Web search with configurable provider (Tavily/Bing) per spec §9.1.
Built as a LangChain tool via @tool decorator.
"""

import json
from typing import Optional

import httpx
from langchain_core.tools import tool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("tools.web_search")


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the public web and return structured results with titles, URLs, and snippets.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
    """
    try:
        if not query or not query.strip():
            return "Error: Empty search query"

        query = query.strip()
        provider = settings.web_search_provider.lower()

        if provider == "tavily" and settings.tavily_api_key:
            result = await _search_tavily(query, max_results)
        elif provider == "bing" and settings.bing_search_api_key:
            result = await _search_bing(query, max_results)
        else:
            logger.warning("No search API key configured, returning simulated results")
            result = _simulated_search(query, max_results)

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Web search error: {e}")
        return json.dumps({"query": query, "results": [], "error": f"Search failed: {str(e)}"})


async def _search_tavily(query: str, max_results: int) -> dict:
    """Search using Tavily API."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
        )
        response.raise_for_status()
        data = response.json()

        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:300],
            }
            for r in data.get("results", [])[:max_results]
        ]
        return {"query": query, "results": results}


async def _search_bing(query: str, max_results: int) -> dict:
    """Search using Bing Search API."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params={"q": query, "count": max_results},
            headers={"Ocp-Apim-Subscription-Key": settings.bing_search_api_key},
        )
        response.raise_for_status()
        data = response.json()

        results = [
            {
                "title": r.get("name", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", "")[:300],
            }
            for r in data.get("webPages", {}).get("value", [])[:max_results]
        ]
        return {"query": query, "results": results}


def _simulated_search(query: str, max_results: int) -> dict:
    """Return simulated search results for demo/development."""
    return {
        "query": query,
        "results": [
            {
                "title": f"Search result for: {query}",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "snippet": f"This is a simulated search result for '{query}'. Configure TAVILY_API_KEY or BING_SEARCH_API_KEY for real results.",
            }
        ],
        "note": "Simulated results — no search API key configured",
    }
