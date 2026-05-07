from .base import LLMProvider, LLMResult
import google.generativeai as genai
import time, os
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions

load_dotenv()    # call this once, at module import time

class GeminiProvider(LLMProvider):

    """LLM provider for Google's gemini models via Google SDK"""

    name="gemini"

    def __init__(self,model:str = "gemini-2.5-flash"):
        super().__init__()
        
        api_key=os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model=model
        self._model=genai.GenerativeModel(model)

    def generate(self, prompt: str) -> LLMResult:

        """Generate result using thje Google Gemini API and return an LLMResult"""
        start=time.perf_counter()

        try:
            response=self._model.generate_content(prompt)
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
            



