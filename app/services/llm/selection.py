"""Which of a provider's models can be picked, parsed from <PROVIDER>_MODELS."""

from dataclasses import dataclass

from app.services.llm.base import ModelInfo

WILDCARD = "*"


@dataclass(frozen=True)
class ModelSelection:
    """Either every model the provider lists ("*") or a fixed list of names.

    An empty selection means the provider is off.
    """

    names: tuple[str, ...] = ()
    wildcard: bool = False

    @classmethod
    def parse(cls, raw: str) -> "ModelSelection":
        names = tuple(dict.fromkeys(n.strip() for n in raw.split(",") if n.strip()))
        if WILDCARD in names:
            return cls(wildcard=True)
        return cls(names=names)

    @property
    def is_empty(self) -> bool:
        return not self.wildcard and not self.names

    @property
    def first(self) -> str | None:
        return self.names[0] if self.names else None

    def allows(self, name: str) -> bool:
        """Whether the name may be picked, judged from the settings alone."""
        return self.wildcard or name in self.names

    def pick(self, offered: list[ModelInfo]) -> tuple[list[ModelInfo], list[str]]:
        """Split against what the provider offers.

        Returns the models that can be picked, and the configured names the
        provider doesn't offer. Configured names keep their configured order.
        """
        if self.wildcard:
            return list(offered), []
        by_name = {m.name: m for m in offered}
        kept = [by_name[n] for n in self.names if n in by_name]
        missing = [n for n in self.names if n not in by_name]
        return kept, missing
