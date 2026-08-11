"""Abstract interface for the generation LLM. TicketSense will pick a concrete provider
later — everything upstream should depend on this interface, not a specific SDK, so
swapping providers doesn't touch the graph/agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    raw: dict | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        """Generate a completion for the given prompt."""


class StubLLMProvider(LLMProvider):
    """Placeholder used until a real provider is wired in, so the rest of the pipeline can
    be built and tested end-to-end without an API key."""

    async def generate(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        return LLMResponse(
            text="[stub-llm] No provider configured yet — set LLM_PROVIDER in .env.",
            raw={"provider": "stub"},
        )
