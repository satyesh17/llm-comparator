from .base import LLMProvider, LLMResult 
import time

class MockProvider(LLMProvider):

    """A mock LLM provider for testing and demonstration purposes."""

    name="mock"
    model="mock-v1"

    def generate(self, prompt: str) -> LLMResult:
        """Simulate generating text by sleeping for the specified latency and returning a fixed output."""
        start=time.perf_counter()
        time.sleep(0.1)

        canned_ouput=f"This is a fake response to : {prompt[:50]}..."
        elapsed_ms = (time.perf_counter() - start) * 1000

        return LLMResult(
            model=self.model,
            output=canned_ouput,
            latency_ms=elapsed_ms,
            input_tokens=len(prompt.split()),  # very naive token count
            output_tokens=len(canned_ouput.split()),  # very naive token count
            cost_usd=0.0
        )

