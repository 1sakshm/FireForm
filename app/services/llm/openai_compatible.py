"""Any server that speaks the OpenAI chat completions API.

That covers OpenAI itself, Gemini and Claude through their compatible endpoints,
Groq, OpenRouter, and self hosted servers like vLLM, LM Studio and llama.cpp.
Only the base URL and the API key differ.
"""

import logging
import re
import time
from contextlib import contextmanager

import openai
import requests

from app.api.schemas.enums import HealthState, LLMProvider
from app.services.llm.base import LLM, PROBE_TIMEOUT_SECONDS, LLMHealth, ModelInfo
from app.services.llm.errors import (
    LLMAuthError,
    LLMError,
    LLMModelNotFoundError,
    LLMRateLimitError,
    LLMResponseError,
    LLMUnavailableError,
)
from app.services.llm.specs import SPECS

logger = logging.getLogger(__name__)


class OpenAICompatibleLLM(LLM):
    def __init__(
        self,
        provider: LLMProvider,
        base_url: str,
        api_key: str,
        model: str | None,
        timeout: int,
        max_retries: int = 3,
        structured_output: bool = True,
        max_tokens: int | None = None,
        temperature: float | None = None,
        headers: dict[str, str] | None = None,
        listed_id_prefix: str = "",
    ):
        super().__init__(provider, model, timeout)
        self.base_url = base_url
        self._secret = api_key or ""
        self.structured_output = structured_output
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.listed_id_prefix = listed_id_prefix or SPECS[provider].listed_id_prefix
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=self._secret or "not-needed",
            timeout=timeout,
            max_retries=max_retries,
            default_headers=headers,
        )

    def _generate(self, prompt: str, schema: dict, model: str) -> str:
        # Optional settings are only sent when set, since some models reject them
        # (OpenAI reasoning models refuse temperature and max_tokens, for example)
        options = {}
        if self.structured_output:
            options["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "form_values", "schema": schema},
            }
        if self.max_tokens is not None:
            options["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            options["temperature"] = self.temperature

        with self._translate_errors(model):
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **options,
            )

        if not completion.choices:
            raise LLMResponseError(f"{self.provider.value} returned no choices")
        choice = completion.choices[0]
        if choice.finish_reason == "length":
            raise LLMResponseError(
                f"{self.provider.value} stopped at the output limit before finishing. "
                f"Raise {SPECS[self.provider].setting('MAX_TOKENS')}."
            )
        return choice.message.content or ""

    def list_models(self) -> list[ModelInfo]:
        probe = self.client.with_options(timeout=PROBE_TIMEOUT_SECONDS, max_retries=0)
        spec = SPECS[self.provider]
        if spec.native_model_list_url:
            models = self._list_native_models(spec)
            if models is None:
                logger.warning(
                    "%s native model listing returned 404 or non-JSON; "
                    "falling back to the compatible model list without capability filtering",
                    self.provider.value,
                )
                models = self._list_compatible_models(probe)
        else:
            models = self._list_compatible_models(probe)

        markers = tuple(marker.lower() for marker in spec.excluded_id_markers)
        if markers:
            models = [
                model for model in models
                if not _has_excluded_id_marker(model.name, markers)
            ]
        return models

    def _list_compatible_models(self, probe) -> list[ModelInfo]:
        with self._translate_errors():
            return [ModelInfo(name=m.id.removeprefix(self.listed_id_prefix)) for m in probe.models.list()]

    def _list_native_models(self, spec) -> list[ModelInfo] | None:
        """List a provider's models with capability metadata; None requests fallback."""
        models: list[ModelInfo] = []
        page_token: str | None = None

        for _ in range(spec.model_list_page_limit):
            params = {"pageToken": page_token} if page_token else {}
            try:
                response = requests.get(
                    spec.native_model_list_url,
                    headers={spec.native_model_list_api_key_header: self._secret},
                    params=params,
                    timeout=PROBE_TIMEOUT_SECONDS,
                )
            except requests.Timeout as exc:
                raise LLMUnavailableError(f"{self.provider.value} model listing timed out") from exc
            except requests.RequestException as exc:
                raise LLMUnavailableError(
                    f"Could not reach {self.provider.value} at {spec.native_model_list_url}."
                ) from exc

            status = response.status_code
            if status == 404:
                return None
            if status in (401, 403):
                raise self._native_auth_error(response)
            if status == 400:
                reason = _native_error_reason(response, self._secret)
                if "api key" in reason.lower():
                    raise self._native_auth_error(response)
                raise LLMResponseError(f"{self.provider.value} refused the model list request with 400: {reason}")
            if status == 429:
                reason = _native_error_reason(response, self._secret)
                raise LLMRateLimitError(f"{self.provider.value} is rate limiting model-list requests: {reason}")
            if status >= 500:
                raise LLMUnavailableError(f"{self.provider.value} had a server error {status}")
            if status >= 400:
                reason = _native_error_reason(response, self._secret)
                raise LLMResponseError(
                    f"{self.provider.value} refused the model list request with {status}: {reason}"
                )

            try:
                body = response.json()
            except ValueError:
                return None
            if not isinstance(body, dict) or not isinstance(body.get("models"), list):
                raise LLMResponseError(f"{self.provider.value} returned an invalid model-list response")

            for item in body["models"]:
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    continue
                methods = item.get("supportedGenerationMethods")
                if (
                    spec.required_generation_method
                    and "supportedGenerationMethods" in item
                    and (
                        not isinstance(methods, list)
                        or spec.required_generation_method not in methods
                    )
                ):
                    continue
                models.append(ModelInfo(name=item["name"].removeprefix(self.listed_id_prefix)))

            page_token = body.get("nextPageToken")
            if not page_token:
                break
        else:
            if page_token:
                logger.warning(
                    "%s native model listing reached the %d-page limit; results may be incomplete",
                    self.provider.value,
                    spec.model_list_page_limit,
                )

        return models

    def _native_auth_error(self, response: requests.Response) -> LLMAuthError:
        return LLMAuthError(
            f"{self.provider.value} rejected the API key: "
            f"{_native_error_reason(response, self._secret)}. "
            f"Check {SPECS[self.provider].setting('API_KEY')}."
        )

    def health(self) -> LLMHealth:
        t0 = time.monotonic()
        try:
            models = self.list_models()
        except LLMError as exc:
            return LLMHealth(status=HealthState.unhealthy, provider=self.provider, detail=exc.message)
        return LLMHealth(
            status=HealthState.healthy,
            provider=self.provider,
            response_time_ms=int((time.monotonic() - t0) * 1000),
            models_available=models or None,
        )

    @contextmanager
    def _translate_errors(self, model: str | None = None):
        """Turn SDK exceptions into LLM errors that say what to fix.

        model is set for a prompt and None for the model list, so a 404 can be
        told apart: a missing model, or a base URL that points somewhere wrong.
        Order matters, subclasses first.
        """
        spec = SPECS[self.provider]
        name = self.provider.value
        try:
            yield
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            raise self._auth_error(exc) from exc
        except openai.RateLimitError as exc:
            raise LLMRateLimitError(
                f"{name} is still rate limiting after retries, or the account is out of quota: "
                f"{_reason(exc, self._secret)}"
            ) from exc
        except openai.APITimeoutError as exc:
            raise LLMUnavailableError(f"{name} at {self.base_url} timed out") from exc
        except openai.APIConnectionError as exc:
            raise LLMUnavailableError(
                f"Could not reach {name} at {self.base_url}. Check {spec.setting('BASE_URL')} and the network."
            ) from exc
        except openai.APIStatusError as exc:
            reason = _reason(exc, self._secret)
            # Gemini answers a bad key with 400 instead of 401
            if exc.status_code == 400 and "api key" in reason.lower():
                raise self._auth_error(exc) from exc
            if exc.status_code == 404 and model:
                raise LLMModelNotFoundError(f"{name} has no model {model}: {reason}") from exc
            if exc.status_code == 404:
                raise LLMResponseError(
                    f"{name} at {self.base_url} has no model list ({reason}). Check {spec.setting('BASE_URL')}."
                ) from exc
            if exc.status_code >= 500:
                raise LLMUnavailableError(f"{name} had a server error {exc.status_code}: {reason}") from exc
            raise LLMResponseError(f"{name} refused the request with {exc.status_code}: {reason}") from exc

    def _auth_error(self, exc: openai.APIStatusError) -> LLMAuthError:
        return LLMAuthError(
            f"{self.provider.value} rejected the API key: {_reason(exc, self._secret)}. "
            f"Check {SPECS[self.provider].setting('API_KEY')}."
        )


def _reason(exc: openai.APIStatusError, secret: object = "") -> str:
    """The provider's own error message, without the JSON around it.

    Bodies differ: OpenAI sends {"error": {"message"}}, Gemini a list of those,
    Anthropic {"type": "error", "error": {"message"}}.
    """
    body = exc.body
    if isinstance(body, list) and body:
        body = body[0]
    message = exc.message.rstrip(".")
    if isinstance(body, dict):
        error = body.get("error", body)
        if isinstance(error, dict) and error.get("message"):
            message = str(error["message"]).rstrip(".")
        elif isinstance(error, str):
            message = error.rstrip(".")
    return _redact_secret(message, secret)


def _native_error_reason(response: requests.Response, secret: str) -> str:
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, list) and body:
        body = body[0]
    if isinstance(body, dict):
        error = body.get("error", body)
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return _redact_secret(error["message"].rstrip("."), secret)
        if isinstance(error, str):
            return _redact_secret(error.rstrip("."), secret)
    return _redact_secret("request rejected", secret)


def _redact_secret(message: str, secret: object) -> str:
    if isinstance(secret, str) and len(secret) >= 8 and secret != "not-needed":
        return message.replace(secret, "[redacted]")
    return message


def _has_excluded_id_marker(model_id: str, markers: tuple[str, ...]) -> bool:
    fragments = re.split(r"[-._]+", model_id.lower())
    for marker in markers:
        marker_fragments = re.split(r"[-._]+", marker.lower())
        width = len(marker_fragments)
        if any(fragments[index:index + width] == marker_fragments for index in range(len(fragments) - width + 1)):
            return True
    return False
