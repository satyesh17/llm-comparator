"""Central Pricing table and cost calculator for LLM models."""

PRICING = {

    # Local Ollama models - all free
    "llama3.1:8b": {"input":0.0, "output":0.0},
    "qwen2.5:7b": {"input":0.0, "output":0.0},
    "mistral:7b": {"input":0.0, "output":0.0},

    # Gemini Free tier
    "gemini-2.5-flash": {"input":0.0, "output":0.0},
    "gemini-2.5-flash-lite": {"input": 0.0, "output": 0.0},

    # HuggingFace / Cerebras free credits
    "meta-llama/Llama-3.1-8B-Instruct:cerebras": {"input":0.0, "output":0.0},
    


    # Reference data for Week 3 paid comparison : 
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.5, "output": 10.0},
   
}

def calculate_cost(model:str, input_tokens:int, output_tokens:int) -> float:

    """Calculate USD cost for a given model + token counts."""
    
    if model not in PRICING:
        return 0.0
    
    rates = PRICING[model]
    input_cost = (input_tokens/1_000_000) * rates["input"]
    output_cost = (output_tokens/1_000_000) * rates["output"]
    return input_cost + output_cost


   