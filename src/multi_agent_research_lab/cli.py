"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import os
from dotenv import load_dotenv
# Load environment variables at the very beginning, before any other imports
load_dotenv()

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

# Set environment variables for tracing libraries immediately
_settings = get_settings()
if _settings.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = _settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = _settings.langsmith_project or "multi-agent-research-lab"

if _settings.langfuse_public_key:
    os.environ["LANGFUSE_PUBLIC_KEY"] = _settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = _settings.langfuse_secret_key or ""
    os.environ["LANGFUSE_HOST"] = _settings.langfuse_host

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()




def _init() -> None:
    """Initialize application settings and logging."""
    settings = get_settings()
    configure_logging(settings.log_level)


import json
from pathlib import Path
from datetime import datetime
from langsmith import traceable
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

@app.command()
@traceable(name="Baseline Research Run", run_type="chain")
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline and save trace locally."""

    _init()
    llm = LLMClient()
    search = SearchClient()
    
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    
    # Simple single-agent flow
    try:
        with console.status("[bold green]Baseline researching..."):
            sources = search.search(query)
            state.sources = sources
            
            source_text = "\n".join([f"- {s.title}: {s.snippet}" for s in sources])
            system_prompt = "You are a helpful assistant. Answer the query based on the search results."
            user_prompt = f"Query: {query}\n\nSources:\n{source_text}"
            
            response = llm.complete(system_prompt, user_prompt)
            state.final_answer = response.content
            
            # Record a simple trace event for baseline
            state.add_trace_event("baseline_llm_call", {"cost": response.cost_usd})
        
        # Save local JSON report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"baseline_{timestamp}.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))
            
        console.print(Panel(state.final_answer, title="Single-Agent Baseline Result"))
        console.print(f"[green]✔ Baseline complete! Local trace saved to: {report_path}[/green]")
        console.print(f"[dim]Cost: ${response.cost_usd:.4f} | Tokens: {response.input_tokens + response.output_tokens}[/dim]")

    except Exception as exc:
        console.print(f"[red]Error during baseline: {exc}[/red]")
        raise exc


@app.command("multi-agent")
@traceable(name="Multi-Agent Research Lab Run", run_type="chain")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow and save trace locally."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    
    try:
        with console.status("[bold blue]Executing Multi-Agent Workflow..."):
            result = workflow.run(state)
        
        # Save local JSON report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"run_{timestamp}.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
            
        console.print(f"\n[green]✔ Workflow complete![/green]")
        console.print(f"[blue]Local trace saved to: {report_path}[/blue]")
        console.print(Panel(result.final_answer or "No final answer generated.", title="Final Output"))
        
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        console.print(f"[red]Error during execution: {exc}[/red]")
        raise exc


if __name__ == "__main__":
    app()
