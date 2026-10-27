"""Assemblage de production : vrais adaptateurs, cache sur disque, clé lue depuis `.env`."""

import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from chatbot_wrc.agent import MODELE_PAR_DEFAUT, Agent
from chatbot_wrc.horloge import HorlogeSysteme
from chatbot_wrc.outils import construire_outils
from chatbot_wrc.transport import TransportHTTP

RACINE = Path(__file__).resolve().parents[2]


def construire_agent() -> Agent:
    load_dotenv(RACINE / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Clé API Anthropic introuvable : copie .env.example en .env et renseigne ANTHROPIC_API_KEY."
        )
    outils = construire_outils(TransportHTTP(), HorlogeSysteme(), RACINE / "cache")
    modele = os.environ.get("CLAUDE_MODELE") or MODELE_PAR_DEFAUT
    return Agent(anthropic.Anthropic(), outils, modele)
