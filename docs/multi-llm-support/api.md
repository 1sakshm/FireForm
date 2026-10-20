# API

Contract: `contracts/path/system.yaml` and `contracts/path/forms.yaml`.

## List providers and models

`GET /api/v1/system/llm/models`

Add `?refresh=true` to skip the cache. Lists are cached for 60 seconds, failures for 10.

```json
{
  "default": { "provider": "gemini", "model": "gemini-2.5-flash" },
  "providers": [
    {
      "provider": "ollama",
      "available": true,
      "default_model": "qwen2.5:1.5b",
      "models": [
        {
          "name": "qwen2.5:1.5b",
          "size_gb": 0.92,
          "quantization": "Q4_K_M",
          "loaded": false
        }
      ]
    },
    {
      "provider": "gemini",
      "available": true,
      "default_model": "gemini-2.5-flash",
      "models": [{ "name": "gemini-2.5-flash" }, { "name": "gemini-2.5-pro" }]
    },
    {
      "provider": "anthropic",
      "available": false,
      "detail": "anthropic rejected the API key: Invalid Anthropic API Key. Check ANTHROPIC_API_KEY.",
      "error_code": "LLM_AUTH_FAILED",
      "models": []
    }
  ]
}
```

- Only enabled providers appear.
- Hosted models carry `name` only. Ollama adds `size_gb`, `quantization` and `loaded`.
- With an explicit `_MODELS` list, names the provider does not offer are left out.
- Empty fields are left out of the response.

## Test a model

`POST /api/v1/system/llm/test`

Sends a short prompt and checks the answer is valid JSON. The body is optional. Missing fields use the defaults.

```json
{ "provider": "ollama", "model": "llama3:8b" }
```

```json
{
  "provider": "ollama",
  "model": "llama3:8b",
  "ok": false,
  "latency_ms": 12,
  "detail": "Ollama has no model llama3:8b. Pull it with: ollama pull llama3:8b",
  "error_code": "LLM_MODEL_NOT_FOUND"
}
```

A failed test returns 200 with `ok: false`. A provider that is not enabled returns 422.

## Fill with a chosen model

`POST /api/v1/forms/fill` and `POST /api/v1/forms/jobs` take two optional fields:

| Field      | Meaning                                                                  |
| ---------- | ------------------------------------------------------------------------ |
| `provider` | One of the enabled providers. Defaults to `LLM_PROVIDER`.                |
| `model`    | A model that provider offers. Defaults to that provider's default model. |

The pair is checked before anything is stored or queued. For jobs, the provider and model are saved on the job and the worker checks them again.

## Health

`GET /api/v1/health` reports the default provider under `components.llm`. Use the models endpoint for the rest.

## Error codes

| Code                  | HTTP | Meaning                                                                |
| --------------------- | ---- | ---------------------------------------------------------------------- |
| `LLM_NOT_AVAILABLE`   | 422  | Provider not enabled, or model not in its list.                        |
| `LLM_CONFIG_ERROR`    | 500  | The LLM settings are wrong. The message names the setting and the fix. |
| `LLM_AUTH_FAILED`     | 502  | The provider rejected the API key.                                     |
| `LLM_MODEL_NOT_FOUND` | 502  | The provider has no such model.                                        |
| `LLM_BAD_RESPONSE`    | 502  | The provider refused the request or did not return JSON.               |
| `LLM_UNAVAILABLE`     | 503  | Could not reach the provider, or it timed out.                         |
| `LLM_RATE_LIMITED`    | 503  | Still rate limited after retries, or out of quota.                     |

Every error body has `error_code` and `message`. 503 responses add `retry_after_seconds`. Failed jobs store the same code and message in `error`.

## Deprecated

`GET /api/v1/forms/models` returns the default provider's model names only. Use `GET /api/v1/system/llm/models`.
