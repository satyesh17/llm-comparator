"""Benchmark structured-output schema-pass-rate across all 5 providers.

Runs each provider on the same set of Enron emails (Yale-LILY/aeslc) plus
one hardcoded "schema parrot" challenge email. Measures:
  - Schema pass rate (% of emails returning valid Pydantic output)
  - Mean latency per provider
  - Per-email failure modes

Outputs:
  - data/schema_benchmark.json — raw results
  - reports/schema_pass_rate_<timestamp>.md — markdown report
"""

import json
import time
from datetime import datetime
from pathlib import Path

from datasets import load_dataset

from src.llm_comparator.providers.gemini_provider import GeminiProvider
from src.llm_comparator.providers.ollama_provider import OllamaProvider
from src.llm_comparator.providers.huggingface_provider import HuggingFaceProvider


# Config
SAMPLE_SIZE = 10              # dev mode; bump to 10 for final
RANDOM_SEED = 42             # same as yesterday
DATASET_NAME = "Yale-LILY/aeslc"
DATA_OUTPUT = Path("data/schema_benchmark.json")
REPORT_DIR = Path("reports")


# The schema-parrot challenge — yesterday's hardest failure case
ANCHOR_EMAIL = {
    "subject": "Enron Article",
    "email_body": (
        "Investing, One Stock=20 =20 Broad Horizons=20 =20 by Jeff Schlegel=20 =20 "
        "December 2000, \"Worth\" magazine=20 =20 Energy giant Enron is expanding its "
        "powerful trading platform into the heart of the U.S. economy. While most "
        "investors focus on the company's role in the deregulated energy markets, "
        "Enron has bigger ambitions. The Houston-based firm now offers contracts on "
        "everything from advertising space to weather derivatives. CEO Jeffrey Skilling "
        "argues this is the future of all commerce: anything that can be standardized "
        "into a contract can be traded. Investors who understand this transformation "
        "stand to profit handsomely from Enron's continued evolution."
    ),
}


def get_providers():
    """Return all 5 providers configured for benchmark."""
    return [
        GeminiProvider(),  # gemini-2.5-flash-lite
        OllamaProvider(model="llama3.1:8b"),
        OllamaProvider(model="qwen2.5:7b"),
        OllamaProvider(model="mistral:7b"),
        HuggingFaceProvider(),  # meta-llama/Llama-3.1-8B-Instruct:cerebras
    ]


def get_emails():
    """Return list of (subject, body) emails to benchmark.
    
    Test 0 is the hardcoded schema-parrot anchor; test 1+ are sampled (seed=42),
    skipping any that match the anchor's subject to avoid duplicates.
    """
    print(f"Loading {DATASET_NAME}...")
    dataset = load_dataset(DATASET_NAME, split="train")
    print(f"  ✅ Loaded {len(dataset):,} emails")
    
    sample = dataset.shuffle(seed=RANDOM_SEED)
    
    emails = [ANCHOR_EMAIL]
    for item in sample:
        if (
            item["email_body"]
            and len(item["email_body"].strip()) >= 10
            and item["subject_line"] != ANCHOR_EMAIL["subject"]
        ):
            emails.append({
                "subject": item["subject_line"],
                "email_body": item["email_body"],
            })
            if len(emails) == SAMPLE_SIZE:
                break
    
    print(f"  ✅ {len(emails)} emails ready (1 anchor + {len(emails) - 1} sampled, dedup applied)")
    return emails


def benchmark(emails, providers):
    """Run all providers on all emails. Returns list of per-email result dicts."""
    all_results = []
    
    for i, email in enumerate(emails):
        print(f"\n[{i+1}/{len(emails)}] {email['subject'][:60]}")
        
        per_email = {
            "email_index": i,
            "subject": email["subject"],
            "preview": email["email_body"][:200],
            "results": [],
        }
        
        for provider in providers:
            tag = f"{provider.name}/{provider.model}"
            print(f"  → {tag}...", end=" ", flush=True)
            
            try:
                result = provider.classify_email(email["email_body"])
                
                per_email["results"].append({
                    "provider": result.provider,
                    "model": result.model,
                    "schema_pass": result.schema_pass,
                    "classification": (
                        result.classification.model_dump()
                        if result.classification else None
                    ),
                    "raw_output": result.raw_output[:300] if result.raw_output else "",
                    "latency_ms": round(result.latency_ms, 1),
                    "error": result.error,
                })
                
                if result.schema_pass:
                    print(f"✅ {result.classification.category}/{result.classification.priority} ({result.latency_ms:.0f}ms)")
                else:
                    print(f"❌ {result.error[:80] if result.error else 'unknown'}")
                
            except Exception as e:
                # Provider crashed entirely (not just classification failed)
                per_email["results"].append({
                    "provider": provider.name,
                    "model": provider.model,
                    "schema_pass": False,
                    "classification": None,
                    "raw_output": "",
                    "latency_ms": 0,
                    "error": f"PROVIDER_CRASH: {type(e).__name__}: {str(e)[:200]}",
                })
                print(f"💥 PROVIDER CRASH: {type(e).__name__}")
        
        all_results.append(per_email)
    
    return all_results


def aggregate(all_results):
    """Compute per-provider schema_pass_rate and mean latency."""
    by_provider = {}
    
    for email in all_results:
        for r in email["results"]:
            tag = f"{r['provider']}/{r['model']}"
            if tag not in by_provider:
                by_provider[tag] = {"pass": 0, "fail": 0, "latencies": [], "errors": []}
            
            if r["schema_pass"]:
                by_provider[tag]["pass"] += 1
            else:
                by_provider[tag]["fail"] += 1
                if r["error"]:
                    by_provider[tag]["errors"].append(r["error"][:120])
            
            if r["latency_ms"] > 0:
                by_provider[tag]["latencies"].append(r["latency_ms"])
    
    # Compute summary stats
    summary = {}
    for tag, data in by_provider.items():
        total = data["pass"] + data["fail"]
        summary[tag] = {
            "pass": data["pass"],
            "fail": data["fail"],
            "total": total,
            "rate": (data["pass"] / total * 100) if total else 0,
            "mean_latency_ms": (
                sum(data["latencies"]) / len(data["latencies"])
                if data["latencies"] else 0
            ),
            "error_samples": data["errors"][:3],  # first 3 unique-ish errors
        }
    
    return summary


def write_report(all_results, summary, report_path):
    """Generate a markdown report."""
    lines = []
    lines.append("# Schema-Pass-Rate Benchmark Report\n")
    lines.append(f"**Generated:** {datetime.now().isoformat()}\n")
    lines.append(f"**Sample size:** {len(all_results)} emails (1 anchor + {len(all_results) - 1} sampled with seed={RANDOM_SEED})\n")
    lines.append(f"**Dataset:** `{DATASET_NAME}`\n\n")
    
    # Headline table
    lines.append("## Schema-Pass-Rate by Provider\n")
    lines.append("| Provider/Model | Schema Pass | Pass Rate | Mean Latency |\n")
    lines.append("|---|---|---|---|\n")
    
    sorted_tags = sorted(summary.keys(), key=lambda t: -summary[t]["rate"])
    for tag in sorted_tags:
        s = summary[tag]
        lines.append(
            f"| `{tag}` | {s['pass']}/{s['total']} | {s['rate']:.1f}% | {s['mean_latency_ms']:.0f}ms |\n"
        )
    
    # Failure modes
    lines.append("\n## Failure Modes\n")
    for tag in sorted_tags:
        s = summary[tag]
        if s["fail"] > 0:
            lines.append(f"\n### `{tag}` — {s['fail']} failure(s)\n")
            for err in s["error_samples"]:
                lines.append(f"- `{err}`\n")
    
    # Anchor email — schema parrot result
    lines.append("\n## Anchor Test (Schema-Parrot Challenge)\n")
    lines.append("This email previously caused 4-validation-error schema-parroting on Llama 3.1 (Groq via Instructor). Per-provider results:\n\n")
    
    anchor = all_results[0]
    lines.append("| Provider/Model | Schema Pass | Latency | Outcome |\n")
    lines.append("|---|---|---|---|\n")
    for r in anchor["results"]:
        tag = f"{r['provider']}/{r['model']}"
        outcome = (
            f"{r['classification']['category']}/{r['classification']['priority']}"
            if r["schema_pass"] else (r['error'][:80] if r['error'] else 'unknown')
        )
        lines.append(
            f"| `{tag}` | {'✅' if r['schema_pass'] else '❌'} | {r['latency_ms']:.0f}ms | {outcome} |\n"
        )
    
    report_path.write_text("".join(lines))
    print(f"\n✅ Report written: {report_path}")


def main():
    print(f"=== Schema-Pass-Rate Benchmark (N={SAMPLE_SIZE}) ===\n")
    
    emails = get_emails()
    providers = get_providers()
    
    print(f"\nProviders: {[f'{p.name}/{p.model}' for p in providers]}")
    print(f"Total LLM calls expected: {len(emails)} × {len(providers)} = {len(emails) * len(providers)}\n")
    
    # Run benchmark
    all_results = benchmark(emails, providers)
    
    # Save raw data
    DATA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUTPUT.write_text(json.dumps(all_results, indent=2))
    print(f"\n✅ Raw data saved: {DATA_OUTPUT}")
    
    # Aggregate + report
    summary = aggregate(all_results)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = REPORT_DIR / f"schema_pass_rate_{timestamp}.md"
    write_report(all_results, summary, report_path)
    
    # Quick console summary
    print("\n=== Final Summary ===\n")
    for tag in sorted(summary.keys(), key=lambda t: -summary[t]["rate"]):
        s = summary[tag]
        print(f"  {tag}")
        print(f"    Pass: {s['pass']}/{s['total']} ({s['rate']:.1f}%) | Mean latency: {s['mean_latency_ms']:.0f}ms")


if __name__ == "__main__":
    main()