import os
from typing import Any

import requests
from dotenv import load_dotenv


SERPER_SEARCH_URL = "https://google.serper.dev/search"
CURRENT_INFO_TERMS = (
    "2026",
    "breaking",
    "current",
    "latest",
    "live",
    "news",
    "now",
    "price",
    "recent",
    "real time",
    "search",
    "today",
    "tomorrow",
    "trending",
    "update",
    "weather",
    "web",
    "yesterday",
)


def should_use_search(query: str) -> bool:
    """Return whether a question is likely to need real-time search."""
    lowered = query.lower()
    return any(term in lowered for term in CURRENT_INFO_TERMS)


def serper_search(query: str, num_results: int = 5) -> list[dict[str, str]]:
    """Fetch concise Google search results through Serper."""
    load_dotenv()
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        return []

    response = requests.post(
        SERPER_SEARCH_URL,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={
            "q": query,
            "num": num_results,
            "gl": "in",
            "hl": "en",
        },
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    return normalize_serper_results(payload, num_results)


def normalize_serper_results(
    payload: dict[str, Any],
    num_results: int = 5,
) -> list[dict[str, str]]:
    """Normalize Serper organic results for prompt context."""
    results = []
    for item in payload.get("organic", [])[:num_results]:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "")).strip()
        link = str(item.get("link", "")).strip()
        snippet = str(item.get("snippet", "")).strip()
        date = str(item.get("date", "")).strip()
        if title and (snippet or link):
            results.append(
                {
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "date": date,
                }
            )
    return results


def format_search_context(results: list[dict[str, str]]) -> str:
    """Format search snippets for the answer prompt."""
    if not results:
        return "No live search results were used."

    lines = []
    for index, result in enumerate(results, start=1):
        date = f" ({result['date']})" if result.get("date") else ""
        lines.append(
            f"{index}. {result['title']}{date}\n"
            f"   Snippet: {result.get('snippet', '')}\n"
            f"   Source: {result.get('link', '')}"
        )
    return "\n".join(lines)
