# llm-comparator

> Benchmark 5 LLMs (local + hosted) on the same prompt — quality, latency, cost, tokens — with LLM-as-judge scoring and Langfuse tracing.

A learning project on my path to **AI Solution Architect**. Demonstrates provider abstraction (Strategy pattern), structured evaluation, observability, retry-with-backoff for rate limits, and cost modeling for production LLM systems.

---

## What it does

This CLI takes a single prompt and runs it through five different LLMs in parallel — three running locally on your laptop via Ollama, two hosted in the cloud — then automatically grades each response using an LLM-as-judge and writes a markdown report comparing latency, token counts, cost, and quality.

The project answers a real interview question every architect faces: **"When would you pick model X over model Y?"** — but with quantitative data, not vibes.

---

## Quick demo

**Prompt:** *"What is badminton? Answer in 2 sentences."*

| Model | Quality | Latency (ms) | In Tokens | Out Tokens | Tok/sec | Cost (USD) |
|---|---|---|---|---|---|---|
| `llama3.1:8b` (local) | 10.0/10 | 11,321 | 22 | 101 | 8.9 | $0.000000 |
| `qwen2.5:7b` (local) | 8.0/10 | 13,101 | 41 | 78 | 6.0 | $0.000000 |
| `mistral:7b` (local) | 10.0/10 | 8,925 | 16 | 81 | 9.1 | $0.000000 |
| `gemini-2.5-flash` (hosted) | 10.0/10 | 3,892 | 11 | 70 | 18.0 | $0.000000 |
| `Llama-3.1-8B-Instruct:cerebras` (hosted) | 10.0/10 | **555** | 47 | 95 | **170.9** | $0.000000 |

The killer datapoint: **the same Llama 3.1 8B model runs ~16× faster on Cerebras's LPU hardware than on a MacBook M-series CPU/GPU.** Same model. Same weights. Different infrastructure.

See [`reports/`](./reports/) for full sample outputs.

---

## Decision matrix — when to pick which model

### Pick local Llama 3.1 8B (or Qwen / Mistral) when…
- You need privacy (HIPAA, GDPR, internal data — nothing leaves the box)
- You can absorb 8–12s cold-start latency, or pre-warm via a cron job firing periodic prompts
- You're prototyping and don't want metered costs
- You're learning AI infrastructure (this project!)

### Pick Gemini 2.5 Flash when…
- You're handling high-volume user-facing requests
- Cost matters more than ~100ms latency differences
- You don't have privacy or data-residency constraints

### Pick Cerebras-hosted Llama when…
- Real-time UX matters (chatbot, voice agent, autocomplete)
- You want open-weights but can't self-host the infrastructure
- Latency consistency is critical (low p99) — Cerebras showed near-zero variance across calls

### Caveats and known limitations
- **Single-prompt benchmarks don't differentiate quality at this difficulty.** Most models score 10/10 on "what is badminton" — meaningful comparison requires harder prompts (math, code, multi-step reasoning). On the roadmap.
- **Self-preference bias risk.** Gemini is both a benchmark target *and* the judge. A more rigorous setup would use a different model (e.g., Claude Opus) as the judge.
- **Free-tier rate limits** cap useful benchmark frequency. Production runs would use paid quotas.
- **Token counts aren't directly comparable** across providers — different tokenizers fragment text differently. $/M token math is approximate until normalized.

---

## How LLM-as-judge works

Every model output is scored 0-10 on a structured rubric:

ACCURACY     (max 5 pts) — Are the facts correct? Penalize hallucinations.
COMPLETENESS (max 3 pts) — Does it fully answer the question?
CLARITY      (max 2 pts) — Is the language clear, precise, and well-written?

The judge (Gemini 2.5 Flash) returns both a score and a 1-2 sentence reasoning, so every score is auditable. Sample reasoning from the run above:

> **`qwen2.5:7b` (8.0/10):** *"The response accurately defines badminton and its gameplay, including singles and doubles, and adheres to the sentence limit. However, it contains a minor grammatical error ('to landing') and inaccurately classifies smashes and drop shots as 'styles of play' rather than types of shots, slightly impacting accuracy and clarity."*

The judge caught a real grammatical and factual nuance that humans would miss on a quick skim. **The rubric IS the eval** — vague rubrics produce noise; structured rubrics produce reliable scores.

---

## Architecture

The project uses the **Strategy pattern**: every LLM provider implements a single abstract interface (`LLMProvider`) returning a normalized `LLMResult`. The CLI (`compare.py`) iterates providers polymorphically — adding a 6th provider (e.g., AWS Bedrock) requires writing one new class, with **zero changes** to the comparison loop, judge, or report generator.

Other key separations:
- **`pricing.py`** — central pricing table (data, not code) for $/M token cost calculations
- **`judge.py`** — LLM-as-judge using Gemini for structured output scoring with JSON schema
- **`retry.py`** — retry-with-backoff for rate-limit handling, honoring the API's own `retry_delay` hint when available
- **Langfuse tracing** — every provider call and judge call is captured as a span in a hierarchical trace

> *Note: this project currently uses `google.generativeai` which is deprecated. Migration to `google.genai` is on the roadmap.*

llm-comparator/
├── compare.py                    # CLI entry point (Click-based)
├── pricing.py                    # central $/M-token lookup table
├── judge.py                      # LLM-as-judge scorer
├── retry.py                      # retry-with-backoff helper
├── src/llm_comparator/
│   └── providers/
│       ├── base.py               # LLMProvider abstract class + LLMResult dataclass
│       ├── ollama_provider.py    # local models via Ollama HTTP
│       ├── gemini_provider.py    # Google Gemini API
│       ├── huggingface_provider.py  # HuggingFace Inference API (with provider routing)
│       └── mock_provider.py      # test fixture (deterministic responses)
├── prompts/                      # benchmark input prompts
├── reports/                      # markdown output, one file per run
├── requirements.txt              # human-curated dependencies
└── requirements-lock.txt         # full transitive dependency lock

---

## Setup & Usage

### 1. Clone the repo
```bash
git clone https://github.com/satyesh17/llm-comparator.git
cd llm-comparator
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API keys
Copy the template and fill in your keys:
```bash
cp .env.example .env
# Edit .env with your editor of choice
```

You'll need:
| Key | Where to get it (free) |
|---|---|
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| `HF_TOKEN` | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| `LANGFUSE_PUBLIC_KEY`<br>`LANGFUSE_SECRET_KEY`<br>`LANGFUSE_HOST` | [cloud.langfuse.com](https://cloud.langfuse.com) |

### 5. Pull local Ollama models *(optional — only for local providers)*
```bash
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull mistral:7b
```

### 6. Run a benchmark
```bash
python compare.py --prompt "What is badminton? Answer in 2 sentences."
```

Or run a batch from a file:
```bash
python compare.py --prompt-file prompts/sample_prompts.txt
```

Reports save to `reports/<timestamp>_<prompt-prefix>.md`.

---

## What I learned

- **Provider abstraction (Strategy pattern) made adding the 5th provider 10× easier than the 1st.** The first OllamaProvider took 2 hours of design + code; the HuggingFaceProvider took 30 minutes because the structure was already established. *This is the architect's dividend on upfront design.*

- **Cold-start vs. warm-state latency is a 30× spread.** Same prompt, same model — first call after idle takes 8-12 seconds; subsequent calls take under 1 second. Production systems must measure both p50 and p99; averages lie.

- **Same model on different hardware: 16× speed difference.** Llama 3.1 8B ran at ~7 tok/sec on a MacBook (Q4 quantized) vs ~115 tok/sec on Cerebras LPUs (FP16 precision). The model isn't the bottleneck — the hardware-and-quantization stack is.

- **LLM-as-judge actually works — but the rubric is the eval.** A vague "rate 1-10" prompt produces inconsistent scores. A structured rubric (accuracy + completeness + clarity, each weighted) produces consistent ones. *The technique is only as good as the criteria.*

- **Rate limits are a structural constraint, not a bug.** Hitting 429s on free-tier APIs is expected. Retry-with-backoff (honoring the API's `retry_delay` hint) is the universal pattern. This applies identically to Gemini, OpenAI, Anthropic, and Bedrock — learning it once compounds.

---

## Roadmap

- **AWS Bedrock provider** — compare Claude Sonnet and Mistral Large at the same abstraction level
- **Migrate to `google.genai`** — current `google.generativeai` is deprecated
- **Multi-prompt benchmark suite** — math, code, multi-step reasoning to differentiate models on harder tasks
- **Token-counting normalization** — different tokenizers make $/M comparisons misleading
- **Self-hosted Langfuse** via Docker (currently using Langfuse Cloud)
- **Concurrent execution** — benchmark runs are serial; parallelizing would cut total time ~5×



---

## Day 3 Extension: Structured Output Reliability

**The question:** When you ask a model for structured JSON output, how reliably does it deliver?

This benchmark answers that question with measured data — running each of 5 providers against the same real-world emails from the Enron corpus (Yale-LILY/aeslc on Hugging Face).

### Headline Result (N=10)

| Provider/Model | Schema Pass | Pass Rate | Mean Latency | Mode |
|---|---|---|---|---|
| `ollama/llama3.1:8b` (local Q4) | 10/10 | **100.0%** | 10,730ms | format=json |
| `ollama/qwen2.5:7b` (local Q4) | 10/10 | **100.0%** | 11,575ms | format=json |
| `huggingface/Llama-3.1-8B:cerebras` | 9/10 | 90.0% | **548ms** | prompted |
| `gemini/gemini-2.5-flash-lite` | 8/10 | 80.0% | 1,845ms | native response_schema |
| `ollama/mistral:7b` (local Q4) | 8/10 | 80.0% | 7,679ms | format=json |

**The counterintuitive headline:** local Ollama models (slowest, weakest enforcement mechanism) achieved the highest schema-pass rates. API providers with native structured output (Gemini) ranked lower. Same Llama 3.1 8B model varies by 10pp depending on hardware (Cerebras FP16 vs. local Q4).

---

### What I Measured

**Methodology:** 10 emails sampled with `seed=42` from Yale-LILY/aeslc (a cleaned Enron subset on Hugging Face). Sample includes 1 anchor email (a quoted-printable encoded news article about Enron, known to trigger schema parroting) and 9 randomly drawn corporate emails (legal redlines, trading ops, charity coordination, etc.).

Each provider was asked to classify each email into the same Pydantic schema:

```python
class EmailClassification(BaseModel):
    category: Literal["sales", "support", "billing", "spam", "other"]
    priority: Literal["low", "medium", "high", "urgent"]
    action_required: bool
    summary: str = Field(min_length=10, max_length=200)
```

Schema-pass-rate = (number of responses passing Pydantic validation) / (total attempts). It measures **output reliability**, not semantic correctness — a model can produce parseable JSON in the wrong category and still "pass."

### Findings

Three findings worth highlighting:

**1. Hardware/quantization affects reliability more than model architecture.**
The same Llama 3.1 8B model achieved different pass rates on different infrastructure: 100% on local CPU/GPU (Q4 quantized), 90% on Cerebras LPUs (FP16). Faster hardware appears to sacrifice some reliability for latency — Cerebras returns in 548ms versus 10,730ms locally, but with one extra failure across 10 trials.

**2. Native structured output is not strictly more reliable than prompted JSON on this benchmark.**
Gemini Flash-Lite uses `response_schema` for API-layer schema enforcement (theoretically the strictest mode), yet achieved 80% — lower than local Llama with `format=json` (weakest mode) at 100%. The reason: Gemini's API enforces *shape* but not *content constraints* like `min_length`/`max_length`. The model can produce summaries that pass the shape check but fail post-validation. **Native schema mode and content constraints are different layers of defense.**

**3. Long document-like emails are systematically harder for all models.**
Test case 7 (a long competitive-analysis email) caused 3 of 5 providers to fail — 60% failure rate on a single email, versus ~5% across all others. The failures clustered into two modes: schema parroting (Mistral, Cerebras) and length-constraint violation (Gemini). Document-shaped input triggers different defects than conversational input.

## License

MIT — see [LICENSE](./LICENSE)

