"""LLM endpoints: GET /api/v1/system/llm/models, POST /api/v1/system/llm/test.

Contract: contracts/path/system.yaml + contracts/schemas/system.yaml
"""

from fastapi import APIRouter

from app.api.schemas.system import LLMModelChoice, LLMModels, LLMProviderModels, LLMTestRequest, LLMTestResult
from app.services import llm

router = APIRouter(prefix="/system/llm", tags=["system"])


# Fields without a value are left out: hosted providers only give a model name,
# Ollama adds size, quantization and whether the model is loaded.
@router.get(
    "/models",
    response_model=LLMModels,
    response_model_exclude_none=True,
    summary="List the LLM providers and models that can fill forms",
)
def list_llm_models(refresh: bool = False):
    registry = llm.get_registry()
    return LLMModels(
        default=LLMModelChoice.model_validate(registry.default),
        providers=[LLMProviderModels.model_validate(c) for c in registry.catalog(refresh)],
    )


@router.post(
    "/test",
    response_model=LLMTestResult,
    response_model_exclude_none=True,
    summary="Check that a model actually answers",
)
def test_llm_model(body: LLMTestRequest | None = None):
    body = body or LLMTestRequest()
    check = llm.ModelValidator(llm.get_registry()).probe(body.provider, body.model)
    return LLMTestResult.model_validate(check)
