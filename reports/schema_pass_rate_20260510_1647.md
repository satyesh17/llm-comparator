# Schema-Pass-Rate Benchmark Report
**Generated:** 2026-05-10T16:47:00.789005
**Sample size:** 10 emails (1 anchor + 9 sampled with seed=42)
**Dataset:** `Yale-LILY/aeslc`

## Schema-Pass-Rate by Provider
| Provider/Model | Schema Pass | Pass Rate | Mean Latency |
|---|---|---|---|
| `ollama/llama3.1:8b` | 10/10 | 100.0% | 10730ms |
| `ollama/qwen2.5:7b` | 10/10 | 100.0% | 11575ms |
| `huggingface/meta-llama/Llama-3.1-8B-Instruct:cerebras` | 9/10 | 90.0% | 548ms |
| `gemini/gemini-2.5-flash-lite` | 8/10 | 80.0% | 1845ms |
| `ollama/mistral:7b` | 8/10 | 80.0% | 7679ms |

## Failure Modes

### `huggingface/meta-llama/Llama-3.1-8B-Instruct:cerebras` — 1 failure(s)
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'desc`

### `gemini/gemini-2.5-flash-lite` — 2 failure(s)
- `ValidationError: 1 validation error for EmailClassification
summary
  String should have at most 200 characters [type=st`
- `ValidationError: 3 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'summ`

### `ollama/mistral:7b` — 2 failure(s)
- `ValidationError: 1 validation error for EmailClassification
category
  Input should be 'sales', 'support', 'billing', 's`
- `ValidationError: 4 validation errors for EmailClassification
category
  Field required [type=missing, input_value={'desc`

## Anchor Test (Schema-Parrot Challenge)
This email previously caused 4-validation-error schema-parroting on Llama 3.1 (Groq via Instructor). Per-provider results:

| Provider/Model | Schema Pass | Latency | Outcome |
|---|---|---|---|
| `gemini/gemini-2.5-flash-lite` | ✅ | 3076ms | other/low |
| `ollama/llama3.1:8b` | ✅ | 9671ms | other/low |
| `ollama/qwen2.5:7b` | ✅ | 14141ms | other/medium |
| `ollama/mistral:7b` | ❌ | 9993ms | ValidationError: 1 validation error for EmailClassification
category
  Input sho |
| `huggingface/meta-llama/Llama-3.1-8B-Instruct:cerebras` | ✅ | 504ms | other/medium |
