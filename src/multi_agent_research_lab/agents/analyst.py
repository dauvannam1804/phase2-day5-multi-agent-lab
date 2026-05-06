"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult


class AnalystAgent(BaseAgent):
    """Synthesizes research notes into deeper analysis and patterns."""

    name = AgentName.ANALYST

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        if not state.research_notes:
            state.errors.append("Analyst ran without research notes.")
            return state

        system_prompt = "You are a senior analyst. Take the provided research notes and synthesize them into deeper insights, identifying trends, gaps, and key takeaways."
        user_prompt = f"Research Notes:\n{state.research_notes}"

        response = self.llm.complete(system_prompt, user_prompt)
        state.analysis_notes = response.content
        
        state.add_trace_event(self.name, {"cost": response.cost_usd})
        state.agent_results.append(AgentResult(agent=self.name, content=response.content))
        
        return state
