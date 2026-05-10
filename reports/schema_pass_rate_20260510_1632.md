# Schema-Pass-Rate Benchmark Report
**Generated:** 2026-05-10T16:32:56.435057
**Sample size:** 5 emails (1 anchor + 4 sampled with seed=42)
**Dataset:** `Yale-LILY/aeslc`

## Schema-Pass-Rate by Provider
| Provider/Model | Schema Pass | Pass Rate | Mean Latency |
|---|---|---|---|
| `ollama/llama3.1:8b` | 4/5 | 80.0% | 19048ms |
| `ollama/qwen2.5:7b` | 4/5 | 80.0% | 22781ms |
| `ollama/mistral:7b` | 4/5 | 80.0% | 17314ms |
| `huggingface/meta-llama/Llama-3.1-8B-Instruct:cerebras` | 3/5 | 60.0% | 636ms |
| `gemini/gemini-2.5-flash-lite` | 2/5 | 40.0% | 1506ms |

## Failure Modes

### `ollama/llama3.1:8b` — 1 failure(s)
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'anal`

### `ollama/qwen2.5:7b` — 1 failure(s)
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'comp`

### `ollama/mistral:7b` — 1 failure(s)
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'comp`

### `huggingface/meta-llama/Llama-3.1-8B-Instruct:cerebras` — 2 failure(s)
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'desc`
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'desc`

### `gemini/gemini-2.5-flash-lite` — 3 failure(s)
- `ValidationError: 1 validation error for EmailClassification
summary
  String should have at most 200 characters [type=st`
- `ValidationError: 1 validation error for EmailClassification
summary
  String should have at most 200 characters [type=st`
- `ValidationError: 1 validation error for EmailClassification
summary
  String should have at most 200 characters [type=st`

## Anchor Test (Schema-Parrot Challenge)
This email previously caused 4-validation-error schema-parroting on Llama 3.1 (Groq via Instructor). Per-provider results:

| Provider/Model | Schema Pass | Latency | Outcome |
|---|---|---|---|
| `gemini/gemini-2.5-flash-lite` | ❌ | 1284ms | ValidationError: 1 validation error for EmailClassification
summary
  String sho |
| `ollama/llama3.1:8b` | ✅ | 10012ms | other/low |
| `ollama/qwen2.5:7b` | ✅ | 16045ms | sales/medium |
| `ollama/mistral:7b` | ✅ | 9773ms | sales/high |
| `huggingface/meta-llama/Llama-3.1-8B-Instruct:cerebras` | ✅ | 482ms | other/medium |
