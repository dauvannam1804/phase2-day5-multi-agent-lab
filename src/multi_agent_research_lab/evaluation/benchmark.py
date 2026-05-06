"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, and record metrics."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    
    # Calculate total cost from agent results if available
    total_cost = 0.0
    for event in state.trace:
        payload = event.get("payload", {})
        total_cost += payload.get("cost", 0.0) if payload else 0.0

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        notes=f"Total agents run: {len(state.route_history)}",
    )
    return state, metrics
