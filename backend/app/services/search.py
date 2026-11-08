import hashlib
from dataclasses import asdict, dataclass

import httpx

from app.config import get_settings

TAVILY_ENDPOINT = "https://api.tavily.com/search"


@dataclass(slots=True)
class SearchDocument:
    title: str
    url: str
    snippet: str
    score: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


class SearchError(RuntimeError):
    pass


class OfflineSearchProvider:
    """Deterministic stand-in so the pipeline is demonstrable without a search key."""

    name = "offline"

    async def search(self, query: str, max_results: int) -> list[SearchDocument]:
        digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
        angles = [
            "background and definitions",
            "current state and recent developments",
            "trade-offs and criticism",
            "practical adoption and outlook",
        ]
        documents = []
        for index in range(min(max_results, len(angles))):
            angle = angles[index]
            documents.append(
                SearchDocument(
                    title=f"{query.strip().title()} - {angle}",
                    url=f"https://example.invalid/{digest[:12]}/{index}",
                    snippet=(
                        f"Offline search result {index + 1} for '{query.strip()}'. "
                        f"This placeholder covers {angle}. Configure SEARCH_PROVIDER=tavily "
                        "with a TAVILY_API_KEY to retrieve real sources."
                    ),
                    score=1.0 - index * 0.1,
                )
            )
        return documents


class TavilySearchProvider:
    name = "tavily"

    def __init__(self, api_key: str, timeout: float) -> None:
        if not api_key:
            raise SearchError("TAVILY_API_KEY is required when SEARCH_PROVIDER=tavily")
        self._api_key = api_key
        self._timeout = timeout

    async def search(self, query: str, max_results: int) -> list[SearchDocument]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(TAVILY_ENDPOINT, json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            raise SearchError(
                f"search provider returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise SearchError(f"search provider unreachable: {exc.__class__.__name__}") from exc
        except ValueError as exc:
            raise SearchError("search provider returned a malformed response") from exc

        documents = []
        for item in body.get("results", []):
            if not isinstance(item, dict):
                continue
            documents.append(
                SearchDocument(
                    title=str(item.get("title", "")).strip(),
                    url=str(item.get("url", "")).strip(),
                    snippet=str(item.get("content", "")).strip()[:1500],
                    score=float(item.get("score", 0.0) or 0.0),
                )
            )
        return documents


def build_search_provider():
    settings = get_settings()
    if settings.search_provider.lower() == "tavily":
        return TavilySearchProvider(settings.tavily_api_key, settings.search_timeout_seconds)
    return OfflineSearchProvider()
