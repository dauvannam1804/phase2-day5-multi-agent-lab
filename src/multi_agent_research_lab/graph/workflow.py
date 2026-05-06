"""LangGraph workflow skeleton."""

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.agents import (
    SupervisorAgent,
    ResearcherAgent,
    AnalystAgent,
    WriterAgent,
)


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.search = SearchClient()
        
        self.supervisor = SupervisorAgent(self.llm)
        self.researcher = ResearcherAgent(self.llm, self.search)
        self.analyst = AnalystAgent(self.llm)
        self.writer = WriterAgent(self.llm)

    def build(self):
        """Create a LangGraph graph."""
        builder = StateGraph(ResearchState)

        # Nodes
        builder.add_node("supervisor", self.supervisor.run)
        builder.add_node("researcher", self.researcher.run)
        builder.add_node("analyst", self.analyst.run)
        builder.add_node("writer", self.writer.run)

        # Edges
        builder.set_entry_point("supervisor")

        # Define conditional edges from supervisor
        def route(state: ResearchState):
            next_agent = state.route_history[-1]
            if next_agent == "done":
                return END
            return next_agent

        builder.add_conditional_edges(
            "supervisor",
            route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                END: END,
            },
        )

        # After each worker, go back to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        app = self.build()
        # LangGraph invoke returns the final state (dict or pydantic)
        final_state_dict = app.invoke(state)
        
        # If it returns a dict, we might need to convert back, 
        # but LangGraph with Pydantic class should work fine.
        if isinstance(final_state_dict, dict):
             return ResearchState(**final_state_dict)
        return final_state_dict
