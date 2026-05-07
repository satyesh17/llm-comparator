
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResult:
    """Normalized result from any LLM provider call."""

    model: str               # "llama3.1:8b", "gemini-2.5-flash", etc.
    output: str              # the actual generated text
    latency_ms: float        # wall-clock time
    input_tokens: int        # tokens read by the model
    output_tokens: int       # tokens generated
    cost_usd: float          # calculated from pricing.py (0 for local)
    error: str | None = None       # populated if something went wrong

class LLMProvider(ABC):

    """Base classes and types shared by all LLM providers."""
    name:str
    model:str


    @abstractmethod
    def generate(self, prompt: str) -> LLMResult:
        """Generate text from the given prompt and return an LLMResult."""
        



