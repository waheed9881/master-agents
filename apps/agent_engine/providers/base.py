"""AI provider adapters for OpenAI, Groq, Gemini, and Mock."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AICompletionResult:
    text: str
    intent: str = "general"
    confidence: float = 0.85
    tokens_used: int = 0
    cost_estimate: float = 0.0
    metadata: dict | None = None


class AIProviderAdapter(ABC):
    """Abstract adapter for LLM providers."""

    provider_name: str = "unknown"

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> AICompletionResult:
        raise NotImplementedError
