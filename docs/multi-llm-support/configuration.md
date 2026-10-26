# Configuration

Every LLM setting, as read from the env file. Empty means unset.

## Rules

- An environment-configured provider is on when its `<PROVIDER>_MODELS` is not empty. A provider configured through the local API is enabled from its saved key or custom URL and uses provider-discovered models.
- Hosted providers also need their API key and `LLM_ALLOW_EXTERNAL=true`.
- A mistake in the default provider blocks every fill until it is fixed. The app still starts and answers with `LLM_CONFIG_ERROR`.
- A mistake in any other provider turns that provider off and logs a warning. The rest keep working.

## Shared settings

| Setting              | Default          | Meaning                                                                       |
| -------------------- | ---------------- | ----------------------------------------------------------------------------- |
| `LLM_PROVIDER`       | `ollama`         | Default provider. One of `ollama`, `openai`, `gemini`, `anthropic`, `custom`. |
| `LLM_MODEL`          | empty            | Default model. Must be allowed by the default provider's `_MODELS`.           |
| `LLM_ALLOW_EXTERNAL` | `false`          | Allow providers outside localhost or a private network.                       |
| `LLM_TIMEOUT`        | `OLLAMA_TIMEOUT` | Seconds per fill.                                                             |
| `LLM_MAX_RETRIES`    | `3`              | Retries on rate limits (429) and server errors (5xx).                         |
| `LLM_TEMPERATURE`    | `0`              | Empty sends none. Some models (OpenAI reasoning models) reject it.            |

## Per provider settings

`<PREFIX>` is `OLLAMA`, `OPENAI`, `GEMINI`, `ANTHROPIC` or `CUSTOM`.

| Setting                      | Meaning                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------- |
| `<PREFIX>_MODELS`            | `*` for every listed model, or a comma separated list. Empty turns the provider off.           |
| `<PREFIX>_API_KEY`           | Environment key: required for OpenAI, Gemini and Anthropic. A local API-saved key can be used instead. Optional for custom. Not used by Ollama. |
| `<PREFIX>_BASE_URL`          | Overrides the provider address. Required for custom. Ollama uses `OLLAMA_HOST` instead.        |
| `<PREFIX>_MAX_TOKENS`        | Output token cap. Empty sends none.                                                            |
| `<PREFIX>_STRUCTURED_OUTPUT` | `true` sends the form's JSON schema as `response_format`. Turn off for servers that reject it. |

## Ollama settings

| Setting          | Default                  | Meaning                                                    |
| ---------------- | ------------------------ | ---------------------------------------------------------- |
| `OLLAMA_HOST`    | `http://localhost:11434` | Ollama address. In Docker use `http://ollama:11434`.       |
| `OLLAMA_MODELS`  | `*`                      | Every pulled model. Empty turns Ollama off.                |
| `OLLAMA_MODEL`   | `qwen2.5:1.5b`           | Ollama's default model, and the one `make fireform` pulls. |
| `OLLAMA_TIMEOUT` | `300`                    | Fallback for `LLM_TIMEOUT`.                                |
| `OLLAMA_PULL_TIMEOUT` | `120`               | Inactivity timeout while streaming a pull (seconds). Not a total time limit: the connect phase uses 10 seconds; each chunk from Ollama resets the inactivity clock. |
| `OLLAMA_INSTALLABLE_MODELS` | empty (built-in default list) | Comma-separated models users may pull when `OLLAMA_MODELS=*`. Ignored when `OLLAMA_MODELS` is an explicit list; then only names in that list can be pulled. |

## Ollama model states

| Term | Meaning |
| ---- | ------- |
| **Default model** | `OLLAMA_MODEL` or `LLM_MODEL` when Ollama is the default provider. Used when a request names no model. |
| **Allowed model** | Named in `OLLAMA_MODELS`, or any tag when `OLLAMA_MODELS=*`. |
| **Installed** | Present on the Ollama host (`ollama list`). Shown in `models` with `installed: true`. |
| **Loaded** | Loaded in memory right now. Ollama adds `loaded: true` on `models`. |
| **Downloadable** | Allowed and not yet installed. Listed under `downloadable` on `GET /system/llm/models`. With `OLLAMA_MODELS=*`, candidates come from `OLLAMA_INSTALLABLE_MODELS` (or the built-in default). With an explicit list, downloadable entries are configured names Ollama does not have yet. |

## Provider defaults

| Provider  | Base URL                                                   | Structured output | Max tokens |
| --------- | ---------------------------------------------------------- | ----------------- | ---------- |
| OpenAI    | `https://api.openai.com/v1`                                | on                | none       |
| Gemini    | `https://generativelanguage.googleapis.com/v1beta/openai/` | on                | none       |
| Anthropic | `https://api.anthropic.com/v1/`                            | off               | `12288`    |
| Custom    | `CUSTOM_BASE_URL`                                          | on                | none       |

## Models shown in the catalog

Gemini models are listed through Gemini's native model-list API. FireForm
removes a model only when Gemini provides `supportedGenerationMethods` and it
does not include `generateContent`; models without that field are retained.
The API key is sent in the `x-goog-api-key` header. If native listing returns
404 or non-JSON, FireForm warns and falls back to the compatible model list
without the capability filter. Listing follows `nextPageToken` for at most 20
pages and warns if that limit is reached.

OpenAI only provides model IDs in its list, so FireForm approximately excludes
IDs containing `embedding`, `whisper`, `tts`, `dall-e`, `moderation`,
`transcribe`, `realtime`, `image` or `audio` (case-insensitive). This is a
name-based heuristic and can be wrong as model names change. Other providers,
including Anthropic, custom servers and Ollama, are not filtered by these
rules. A filtered model can still be entered and tested as a manual model.

Filtering applies at the provider model-list source. It therefore affects the
catalog, startup `check_config()` and candidate configuration validation. A
filtered configured name is treated as missing and gets the usual warning.
The configured default model is not replaced automatically: startup warns that
it is not offered and fills will fail, and FireForm does not switch to another
provider. The existing `probe(..., verify=False)` path used by
`POST /system/llm/test` and manual-model registration remains an intentional
escape hatch; a model added manually is included in the catalog even if the
provider's list filter would exclude it.

## What counts as local

A URL is local when its host is `localhost`, a loopback or private IP, a bare name such as a Docker service (`vllm`, `ollama`), or ends in `.local`, `.internal` or `.lan`. Anything else needs `LLM_ALLOW_EXTERNAL=true`.

## Docker

Both compose files load the env file into the app and the worker, so every setting above reaches both containers. They also share a persistent `llm_secrets` volume for the generated master key. Do not repeat LLM settings under `environment:` in a compose file. Values there override the env file.

The local provider API, credential encryption key, and single-user limitations
are described in [User configuration](user-configuration.md).

## Removed settings

| Old                     | Use instead                                                   |
| ----------------------- | ------------------------------------------------------------- |
| `LLM_BASE_URL`          | `CUSTOM_BASE_URL`, `OLLAMA_HOST` or `<PREFIX>_BASE_URL`       |
| `LLM_API_KEY`           | `CUSTOM_API_KEY`. Hosted providers no longer fall back to it. |
| `LLM_MAX_TOKENS`        | `<PREFIX>_MAX_TOKENS`                                         |
| `LLM_STRUCTURED_OUTPUT` | `<PREFIX>_STRUCTURED_OUTPUT`                                  |
