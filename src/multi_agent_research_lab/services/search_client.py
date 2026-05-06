"""Search client abstraction for ResearcherAgent."""

from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import SourceDocument


from multi_agent_research_lab.core.config import get_settings
import httpx


class SearchClient:
    """Provider-agnostic search client implementation using Tavily."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query using Tavily."""
        if not self.settings.tavily_api_key:
            # Fallback to a mock for lab purposes if key is missing
            return [
                SourceDocument(
                    title="Mock Result (No Tavily API Key)",
                    url="https://example.com",
                    snippet=f"This is a mock result for query: {query}",
                )
            ]

        try:
            response = httpx.post(
                self.api_url,
                json={
                    "api_key": self.settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    SourceDocument(
                        title=item.get("title", "No Title"),
                        url=item.get("url"),
                        snippet=item.get("content", item.get("snippet", "")),
                    )
                )
            return results
        except Exception as e:
            # Return empty list or mock on error to keep flow going
            print(f"Search error: {e}")
            return []
