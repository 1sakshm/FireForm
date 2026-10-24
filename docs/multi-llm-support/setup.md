# Setup

All settings live in `docker/.env.dev` (development) or `docker/.env.prod` (production). Start from `docker/.env.example`.

## 1. Pick the providers

Set `<PROVIDER>_MODELS` for each provider you want on. Leave it empty to keep a provider off.

```
OLLAMA_MODELS=*
GEMINI_API_KEY=...
GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-pro
ANTHROPIC_API_KEY=...
ANTHROPIC_MODELS=claude-sonnet-5-5
```

`*` offers every model the provider lists. A comma separated list offers only those names.

## 2. Allow hosted providers

OpenAI, Gemini and Anthropic send incident data off the machine. Turn them on deliberately:

```
LLM_ALLOW_EXTERNAL=true
```

## 3. Set the default

The default answers every fill that names no provider or model.

```
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
```

If `LLM_MODEL` is empty, Ollama uses `OLLAMA_MODEL` and the other providers use the first name in their `_MODELS` list.

## 4. Apply the changes

```
make up
```

`make up` recreates the app and worker containers so they read the new env file. A plain restart keeps the old values.

## 5. Check it

Look for these lines in `make logs-app`:

```
LLM default: gemini gemini-2.5-flash. Enabled providers: ollama, gemini, anthropic
LLM settings: <one line per problem found>
```

Then confirm from the API:

```
curl http://localhost:8000/api/v1/system/llm/models
curl -X POST http://localhost:8000/api/v1/system/llm/test \
  -H 'Content-Type: application/json' \
  -d '{"provider": "gemini", "model": "gemini-2.5-flash"}'
```

A test that returns `"ok": true` means the model answered a real prompt.

## Common setups

**Local only (default)**

```
LLM_PROVIDER=ollama
OLLAMA_MODELS=*
```

**Ollama default, Gemini as an option**

```
LLM_PROVIDER=ollama
LLM_ALLOW_EXTERNAL=true
GEMINI_API_KEY=...
GEMINI_MODELS=gemini-2.5-flash
```

**Self hosted vLLM only, Ollama off**

```
LLM_PROVIDER=custom
OLLAMA_MODELS=
CUSTOM_BASE_URL=http://vllm:8000/v1
CUSTOM_MODELS=Qwen/Qwen2.5-7B-Instruct
```

**Ollama on the host machine (Metal or GPU)**

```
OLLAMA_HOST=http://host.docker.internal:11434
```

Run `make fireform-native` (later `make up-native`). The model must already be pulled where Ollama runs.
