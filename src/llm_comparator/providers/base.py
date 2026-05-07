
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResult:
    """Normalized result from any LLM provider call."""
    
    model: str
    output: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: str | None = None
    quality_score: float | None = None      # ← NEW
    quality_reasoning: str | None = None    # ← NEW

class LLMProvider(ABC):

    """Base classes and types shared by all LLM providers."""
    name:str
    model:str


    @abstractmethod
    def generate(self, prompt: str) -> LLMResult:
        """Generate text from the given prompt and return an LLMResult."""
        



