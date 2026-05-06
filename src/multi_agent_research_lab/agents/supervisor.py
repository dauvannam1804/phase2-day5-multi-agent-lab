"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.config import get_settings


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = AgentName.SUPERVISOR

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        
        # Enforce max iterations
        if state.iteration >= self.settings.max_iterations:
            state.record_route("done")
            return state

        # Simple logic: Researcher -> Analyst -> Writer -> Done
        # Or use LLM for dynamic routing
        
        system_prompt = (
            "You are a research supervisor. Based on the current state, decide which agent should run next.\n"
            "Options: researcher, analyst, writer, done.\n"
            "Guidelines:\n"
            "1. If no research notes exist, pick 'researcher'.\n"
            "2. If research notes exist but no analysis exists, pick 'analyst'.\n"
            "3. If analysis exists but no final answer exists, pick 'writer'.\n"
            "4. If everything is complete, pick 'done'."
        )
        
        user_prompt = (
            f"Query: {state.request.query}\n"
            f"Research Notes: {'Yes' if state.research_notes else 'No'}\n"
            f"Analysis: {'Yes' if state.analysis_notes else 'No'}\n"
            f"Final Answer: {'Yes' if state.final_answer else 'No'}\n"
            f"Iteration: {state.iteration}"
        )

        response = self.llm.complete(system_prompt, user_prompt)
        next_agent = response.content.lower().strip()
        
        # Validation
        valid_agents = ["researcher", "analyst", "writer", "done"]
        if next_agent not in valid_agents:
            # Fallback
            if not state.research_notes: next_agent = "researcher"
            elif not state.analysis_notes: next_agent = "analyst"
            elif not state.final_answer: next_agent = "writer"
            else: next_agent = "done"

        state.record_route(next_agent)
        state.add_trace_event(self.name, {"next_agent": next_agent, "iteration": state.iteration})
        
        return state
