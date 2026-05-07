"""CLI to benchmark a prompt across multiple LLM providers."""

# Standard library
from datetime import datetime
from pathlib import Path

# Third-party
import click

# Local — your own package
from src.llm_comparator.providers.ollama_provider import OllamaProvider
from src.llm_comparator.providers.gemini_provider import GeminiProvider
from src.llm_comparator.providers.huggingface_provider import HuggingFaceProvider
from src.llm_comparator.pricing import calculate_cost

from src.llm_comparator.judge import Judge, JudgeResult

def get_providers():
    """Return the list of providers to benchmark"""
    return [
        OllamaProvider(model="llama3.1:8b"),
        OllamaProvider(model="qwen2.5:7b"),
        OllamaProvider(model="mistral:7b"),
        GeminiProvider(model="gemini-2.5-flash"),
        HuggingFaceProvider(model="meta-llama/Llama-3.1-8B-Instruct:cerebras"),
    ]

def run_comparison(prompt: str):
    """Call every provider, then judge each output."""
    providers = get_providers()
    judge = Judge()    # ← NEW: create judge once
    results = []
    
    for provider in providers:
        click.echo(f"Calling {provider.name}/{provider.model}...")
        result = provider.generate(prompt)
        
        result.cost_usd = calculate_cost(
            result.model,
            result.input_tokens,
            result.output_tokens,
        )
        
        results.append(result)
    
    # Judge after all generations are done (less interleaved API noise)
    click.echo("\nJudging responses...")
    for result in results:
        if result.error:
            continue    # don't judge failed responses
        
        judgment = judge.score(prompt, result.output)
        result.quality_score = judgment.score
        result.quality_reasoning = judgment.reasoning
    
    return results

def write_report(prompt: str, results: list, output_dir: Path = Path("reports")):
    """Write a markdown comparison report."""
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
    report_path = output_dir / f"{timestamp}_{safe_prompt}.md"
    
    with open(report_path, "w") as f:
        f.write("# LLM Comparison Report\n\n")
        f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
        f.write(f"**Prompt:** {prompt}\n\n")
        f.write("---\n\n## Summary\n\n")
        # ↓ NEW: added "Quality" column
        f.write("| Model | Quality | Latency (ms) | In Tokens | Out Tokens | Tok/sec | Cost (USD) | Status |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        
        for r in results:
            tps = r.output_tokens / (r.latency_ms / 1000) if r.latency_ms else 0
            status = "❌" if r.error else "✅"
            quality = f"{r.quality_score:.1f}/10" if r.quality_score is not None else "—"
            f.write(
                f"| `{r.model}` | {quality} | {r.latency_ms:.1f} | {r.input_tokens} | "
                f"{r.output_tokens} | {tps:.1f} | ${r.cost_usd:.6f} | {status} |\n"
            )
        
        f.write("\n---\n\n## Outputs\n\n")
        for r in results:
            f.write(f"### {r.model}\n\n")
            if r.error:
                f.write(f"**ERROR:** {r.error}\n\n")
            else:
                f.write(f"{r.output}\n\n")
                # ↓ NEW: judge reasoning
                if r.quality_reasoning:
                    f.write(f"\n**Judge ({r.quality_score:.1f}/10):** {r.quality_reasoning}\n\n")
            f.write("---\n\n")
    
    return report_path


@click.command()
@click.option("--prompt", "-p", help="Prompt to send to all providers")
@click.option("--prompt-file", "-f", type=click.Path(exists=True),
              help="Text file with one prompt per line")
def main(prompt: str, prompt_file: str):
    """Benchmark multiple LLM providers on the same prompt."""
    if prompt_file:
        with open(prompt_file) as f:
            prompts = [line.strip() for line in f if line.strip()]
    elif prompt:
        prompts = [prompt]
    else:
        click.echo("Error: provide --prompt or --prompt-file")
        return
    
    for p in prompts:
        click.echo(f"\n=== Benchmarking: {p[:60]}... ===\n")
        results = run_comparison(p)
        report_path = write_report(p, results)
        click.echo(f"\n✅ Report saved: {report_path}\n")


if __name__ == "__main__":
    main()