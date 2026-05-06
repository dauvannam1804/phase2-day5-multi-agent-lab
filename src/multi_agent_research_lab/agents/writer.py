"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult


class WriterAgent(BaseAgent):
    """Produces the final polished report or answer."""

    name = AgentName.WRITER

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        if not state.analysis_notes:
            state.errors.append("Writer ran without analysis notes.")
            return state

        system_prompt = f"You are a technical writer. Write a final, polished report for an audience of {state.request.audience}."
        user_prompt = f"Original Query: {state.request.query}\n\nResearch Notes:\n{state.research_notes}\n\nAnalysis Insights:\n{state.analysis_notes}"

        response = self.llm.complete(system_prompt, user_prompt)
        state.final_answer = response.content
        
        state.add_trace_event(self.name, {"cost": response.cost_usd})
        state.agent_results.append(AgentResult(agent=self.name, content=response.content))
        
        return state
