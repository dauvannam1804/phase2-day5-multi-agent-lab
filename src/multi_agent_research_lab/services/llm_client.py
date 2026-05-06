"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass

from multi_agent_research_lab.core.errors import StudentTodoError


from multi_agent_research_lab.core.config import get_settings
from openai import OpenAI


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


from langsmith import traceable
from langfuse.openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai


class LLMClient:
    """Provider-agnostic LLM client implementation using OpenAI with fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
        )

    @traceable(run_type="llm", name="LLM Completion")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, openai.RateLimitError)),
        reraise=False,  # We want to catch it ourselves for a final fallback
    )
    def _call_model(self, model: str, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Internal method to call the model with retry logic."""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        # Simple cost calculation for gpt-4o-mini / gpt-5-nano
        cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with primary and secondary fallback."""
        try:
            # Attempt primary model
            return self._call_model(self.settings.openai_model, system_prompt, user_prompt)
        except Exception as e:
            print(f"Primary model ({self.settings.openai_model}) failed: {e}")
            
            # Fallback to a secondary model if primary is not gpt-4o-mini
            fallback_model = "gpt-4o-mini"
            if self.settings.openai_model != fallback_model:
                try:
                    print(f"Attempting fallback to {fallback_model}...")
                    return self._call_model(fallback_model, system_prompt, user_prompt)
                except Exception as fe:
                    print(f"Fallback model also failed: {fe}")
            
            # Final fallback: Return an error message as content so the workflow doesn't crash
            return LLMResponse(
                content="I encountered an error while processing your request. Please try again later.",
                cost_usd=0.0
            )
