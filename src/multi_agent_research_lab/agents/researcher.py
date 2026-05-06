"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = AgentName.RESEARCHER

    def __init__(self, llm: LLMClient, search: SearchClient) -> None:
        self.llm = llm
        self.search = search

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        query = state.request.query
        
        # 1. Search for sources
        sources = self.search.search(query, max_results=state.request.max_sources)
        state.sources.extend(sources)
        
        # 2. Synthesize research notes using LLM
        source_text = "\n\n".join([f"Source: {s.title}\nURL: {s.url}\nContent: {s.snippet}" for s in sources])
        
        system_prompt = "You are a professional researcher. Summarize the provided search results into structured research notes."
        user_prompt = f"Query: {query}\n\nSearch Results:\n{source_text}"
        
        response = self.llm.complete(system_prompt, user_prompt)
        state.research_notes = response.content
        
        # 3. Record trace
        state.add_trace_event(self.name, {"sources_count": len(sources), "cost": response.cost_usd})
        state.agent_results.append(AgentResult(agent=self.name, content=response.content))
        
        return state
