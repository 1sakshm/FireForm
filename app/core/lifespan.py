"""Application lifespan: startup and shutdown hooks."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.init_db import init_db
from app.services import llm

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    await asyncio.to_thread(_check_llm_settings)
    yield


def _check_llm_settings() -> None:
    """Log what the LLM settings enable, and anything wrong with them.

    Wrong settings don't stop the app. Everything that needs an LLM answers
    with LLM_CONFIG_ERROR and the same message until they are fixed, so the
    frontend can show it instead of finding no backend at all.
    """
    try:
        registry = llm.get_registry()
    except llm.LLMConfigError as exc:
        logger.error(
            "LLM settings need fixing, forms can't be filled until they are.\n"
            "    %s\n"
            "    Change the env file (docker/.env.dev or docker/.env.prod), then run make up.",
            exc.message,
        )
        return

    default = registry.default
    logger.info(
        "LLM default: %s %s. Enabled providers: %s",
        default.provider.value, default.model, ", ".join(p.value for p in registry.providers),
    )
    for warning in llm.ModelValidator(registry).check_config():
        logger.warning("LLM settings: %s", warning)
