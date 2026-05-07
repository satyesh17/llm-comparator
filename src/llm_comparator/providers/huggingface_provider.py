

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from .base import LLMProvider, LLMResult
import time, os
from dotenv import load_dotenv
from langfuse import observe


load_dotenv()    # call this once, at module import time

class HuggingFaceProvider(LLMProvider):

    """LLM provider for HuggingFace API provider — calls open-source models on HF's infra"""
    
    name="huggingface"
    
    def __init__(self,model:str="meta-llama/Llama-3.1-8B-Instruct:cerebras"):
        
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise ValueError("HF_TOKEN not found. Add it to your .env file.")
        self.model=model
        self._client=InferenceClient(model=model,token=token)


    @observe(name="huggingface_generate", as_type="generation")
    def generate(self, prompt: str) -> LLMResult:

        """Generate result using the HuggingFace Inference API and return an LLMResult"""
        start=time.perf_counter()

        try:
            response = self._client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
)
            elapsed_ms=(time.perf_counter()-start)*1000

            return LLMResult(
                model=self.model,
                output=response.choices[0].message.content,
                latency_ms=elapsed_ms,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                cost_usd=0.0,
            )
        
        except HfHubHTTPError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return LLMResult(
                model=self.model,
                output="",
                latency_ms=elapsed_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                error=f"HuggingFace API error: {e}",
            )
        
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return LLMResult(
                model=self.model,
                output="",
                latency_ms=elapsed_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                error=f"Unexpected error: {e}",
            )




        