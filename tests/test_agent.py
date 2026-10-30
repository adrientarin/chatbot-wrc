"""L'agent ne demande le rattrapage des refus qu'aux modèles qui l'ont."""

from types import SimpleNamespace
from typing import Any, cast

import anthropic
import pytest

from chatbot_wrc.agent import Agent
from chatbot_wrc.outils import Outils


class FauxMessages:
    def __init__(self) -> None:
        self.options: dict[str, Any] = {}

    def create(self, **options: Any) -> SimpleNamespace:
        self.options = options
        return SimpleNamespace(
            stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Salut !")]
        )


def options_envoyees(modele: str) -> dict[str, Any]:
    messages = FauxMessages()
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    Agent(cast(anthropic.Anthropic, client), cast(Outils, None), modele).repondre("Salut")
    return messages.options


@pytest.mark.parametrize("modele", ["claude-sonnet-5-5", "claude-opus-5-5"])
def test_un_modele_avec_rattrapage_le_demande(modele: str) -> None:
    options = options_envoyees(modele)

    assert options["fallbacks"] == "default"
    assert options["betas"] == ["server-side-fallback-2026-07-01"]


def test_haiku_ne_demande_pas_de_rattrapage() -> None:
    options = options_envoyees("claude-haiku-5-5")

    assert "fallbacks" not in options
    assert "betas" not in options
