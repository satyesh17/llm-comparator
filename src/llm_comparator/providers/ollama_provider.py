from .base import LLMProvider, LLMResult
import os, requests, time
from dotenv import load_dotenv
from langfuse import observe

import json
import time
from pydantic import ValidationError

from ..email_models import EmailClassification, EmailClassificationResult

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

    @observe(name="ollama_generate", as_type="generation")
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
        
    def classify_email(self, email_text: str) -> EmailClassificationResult:
        """Classify an email using Ollama's format=json (no schema enforcement)."""
        result = EmailClassificationResult(
            provider="ollama",
            model=self.model,
            )
    
        schema_str = json.dumps(EmailClassification.model_json_schema(), indent=2)
        '''prompt = f"""You are an email classification system. Return ONLY a JSON object matching this schema:
        {schema_str}
        
        EMAIL:
        {email_text}
        
        Return ONLY the JSON object, no preamble or explanation."""'''

        prompt = f"""You are an email classification system. Return ONLY a JSON object matching this schema:

            {schema_str}

            The summary field MUST be at least 10 characters and at most 200 characters, describing the email's content and purpose.

            EMAIL:
            {email_text}

            Return ONLY the JSON object, no preamble or explanation."""
    
        start = time.perf_counter()
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Ollama's only structured-output knob
                },
                timeout=120,
            )
            response.raise_for_status()
            body = response.json()
            result.raw_output = body.get("response", "")
            result.latency_ms = (time.perf_counter() - start) * 1000
            
            # Parse + validate
            parsed = json.loads(result.raw_output)
            result.classification = EmailClassification.model_validate(parsed)
            result.schema_pass = True
            
        except ValidationError as e:
            result.latency_ms = (time.perf_counter() - start) * 1000
            result.error = f"ValidationError: {str(e)[:200]}"
        except json.JSONDecodeError as e:
            result.latency_ms = (time.perf_counter() - start) * 1000
            result.error = f"JSONDecodeError: {str(e)[:200]}"
        except Exception as e:
            result.latency_ms = (time.perf_counter() - start) * 1000
            result.error = f"{type(e).__name__}: {str(e)[:200]}"
        
        return result