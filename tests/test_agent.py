"""L'agent ne demande le rattrapage des refus qu'aux modèles qui l'ont."""

import threading
import time
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


class FauxMessagesLents:
    """Comme l'API, demande un outil puis répond, et note les appels qui se chevauchent."""

    def __init__(self) -> None:
        self.en_cours = 0
        self.max_en_cours = 0
        self.verrou = threading.Lock()

    def create(self, **options: Any) -> SimpleNamespace:
        with self.verrou:
            self.en_cours += 1
            self.max_en_cours = max(self.max_en_cours, self.en_cours)
        time.sleep(0.05)
        with self.verrou:
            self.en_cours -= 1
        if isinstance(options["messages"][-1]["content"], str):
            appel = SimpleNamespace(type="tool_use", id="toolu_1", name="calendrier", input={})
            return SimpleNamespace(stop_reason="tool_use", content=[appel])
        return SimpleNamespace(
            stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Salut !")]
        )


def test_deux_questions_simultanees_ne_melangent_pas_l_historique() -> None:
    # Streamlit peut lancer une 2e question pendant que la 1re attend encore sa réponse.
    messages = FauxMessagesLents()
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    outils = SimpleNamespace(executer=lambda nom, arguments: {})
    agent = Agent(cast(anthropic.Anthropic, client), cast(Outils, outils), "claude-haiku-5-5")
    depart = threading.Barrier(2)

    def poser(question: str) -> None:
        depart.wait()
        agent.repondre(question)

    fils = [threading.Thread(target=poser, args=(q,)) for q in ("Un", "Deux")]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    assert messages.max_en_cours == 1
    assert [m["role"] for m in agent._messages] == ["user", "assistant", "user", "assistant"] * 2
