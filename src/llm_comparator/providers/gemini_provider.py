from .base import LLMProvider, LLMResult
import google.generativeai as genai
import time, os
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions
from langfuse import observe
from ..retry import retry_with_backoff
            
import json
import time
from pydantic import ValidationError

from ..email_models import EmailClassification, EmailClassificationResult, EmailClassificationLite

load_dotenv()    # call this once, at module import time


class GeminiProvider(LLMProvider):

    """LLM provider for Google's gemini models via Google SDK"""

    name="gemini"

    

    def __init__(self,model:str = "gemini-2.5-flash-lite"):
        super().__init__()
        
        api_key=os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model=model
        self._model=genai.GenerativeModel(model)

    @observe(name="gemini_generate", as_type="generation")

    def generate(self, prompt: str) -> LLMResult:

        """Generate result using the Google Gemini API and return an LLMResult"""
        start=time.perf_counter()

        try:
            response=retry_with_backoff(lambda: self._model.generate_content(prompt))
            elapsed_ms=(time.perf_counter()-start)*1000

            return LLMResult(
                model=self.model,
                output=response.text,
                latency_ms=elapsed_ms,
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count,
                cost_usd=0.0,
            )




        except google_exceptions.GoogleAPIError as e: # Catches all Google API errors — rate limits, auth failures, etc.
            elapsed_ms=(time.perf_counter()-start)*1000

            return LLMResult(
                model=self.model,
                output="",
                latency_ms=elapsed_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                error=f"Google API error: {e}",
                )
        except Exception as e: # Catch-all for anything unexpected
            return LLMResult(
                model=self.model,
                output="",
                latency_ms=elapsed_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                error=f"Google API error: {e}",
                )



    def classify_email(self, email_text: str) -> EmailClassificationResult:
        """Classify an email using Gemini's native response_schema mode."""
        result = EmailClassificationResult(
            provider="gemini",
            model=self.model,
        )
        
        #prompt = f"Classify the following email into the structured schema.\n\nEMAIL:\n{email_text}"
        prompt = (
            "Classify the following email into the JSON schema. "
            "Provide a summary of at least 10 characters and at most 200 characters "
            "describing the email's content and purpose. "
            "Return ONLY the JSON object.\n\n"
            f"EMAIL:\n{email_text}"
            )
        
        start = time.perf_counter()
        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": EmailClassificationLite,
                },
            )
            result.raw_output = response.text
            result.latency_ms = (time.perf_counter() - start) * 1000
            
            # Parse + validate
            parsed = json.loads(response.text)
            result.classification = EmailClassification.model_validate(parsed)
            result.schema_pass = True
            
        except ValidationError as e:
            result.latency_ms = (time.perf_counter() - start) * 1000
            result.error = f"ValidationError: {str(e)[:200]}"
        except Exception as e:
            result.latency_ms = (time.perf_counter() - start) * 1000
            result.error = f"{type(e).__name__}: {str(e)[:200]}"
        
        return result



