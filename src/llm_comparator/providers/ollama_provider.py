from .base import LLMProvider, LLMResult
import os, requests, time
from dotenv import load_dotenv
load_dotenv()    # call this once, at module import time

class OllamaProvider(LLMProvider):

    """LLM provider for Ollama models that are running locally"""

    name = "ollama"


    def __init__(self,model:str,base_url:str | None = None):


        super().__init__()
        self.model=model
        self.base_url=(base_url 
                       or os.environ.get("OLLAMA_BASE_URL") 
                       or "http://localhost:11434")

    def generate(self, prompt: str) -> LLMResult:

        """Generate text using the Ollama API and return an LLMResult."""
        start = time.perf_counter()
    
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model, 
                    "prompt": prompt, 
                    "stream": False,
                    },
                timeout=200,    # don't hang forever
            )
            response.raise_for_status()    # raises if HTTP 4xx/5xx
            data = response.json()
            
            return LLMResult(
                model=self.model,
                output=data["response"],
                latency_ms=data["total_duration"] / 1_000_000,
                input_tokens=data["prompt_eval_count"],
                output_tokens=data["eval_count"],
                cost_usd=0.0,
            )
        
        except requests.exceptions.RequestException as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return LLMResult(
                model=self.model,
                output="",
                latency_ms=elapsed_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                error=f"Request failed: {e}",
            )