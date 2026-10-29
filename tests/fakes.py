"""Faux adaptateurs injectés dans le module source WRC pendant les tests."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from chatbot_wrc.outils import Outils, construire_outils
from chatbot_wrc.transport import ErreurTransport

FIXTURES = Path(__file__).parent / "fixtures"

# Fichier de fixture servi pour chaque fin d'adresse de l'API.
_ROUTES = {
    "seasons.json": "seasons.json",
    "season-detail.json?seasonId=47": "season-detail-47.json",
    "season-detail.json?seasonId=50": "season-detail-50.json",
    **{
        f"championship-{quoi}.json?championshipId={championnat}&seasonId={saison}": (
            f"championship-{quoi}-{championnat}.json"
        )
        for quoi in ("detail", "overall-results")
        for saison, championnats in ((47, (333, 334, 335, 337, 338)), (50, (374, 375, 376)))
        for championnat in championnats
    },
}


def fixture(nom: str) -> Any:
    return json.loads((FIXTURES / nom).read_text(encoding="utf-8"))


class FauxTransport:
    """Sert les fixtures enregistrées, ou simule une panne ou un format inattendu."""

    def __init__(self) -> None:
        self.en_panne = False
        self.appels: list[str] = []
        self._remplacements: dict[str, str] = {}

    def remplacer(self, fin_adresse: str, contenu: Any) -> None:
        """Sert `contenu` (objet JSON ou texte brut) à la place de la fixture."""
        self._remplacements[fin_adresse] = (
            contenu if isinstance(contenu, str) else json.dumps(contenu)
        )

    def get(self, url: str) -> str:
        self.appels.append(url)
        if self.en_panne:
            raise ErreurTransport(f"panne simulée sur {url}")
        for fin, contenu in self._remplacements.items():
            if url.endswith(fin):
                return contenu
        for fin, nom in _ROUTES.items():
            if url.endswith(fin):
                return (FIXTURES / nom).read_text(encoding="utf-8")
        raise ErreurTransport(f"404 simulé sur {url}")


class FausseHorloge:
    def __init__(self, maintenant: datetime) -> None:
        self._maintenant = maintenant

    def maintenant(self) -> datetime:
        return self._maintenant

    def avancer(self, duree: timedelta) -> None:
        self._maintenant += duree


def outils(
    transport: FauxTransport, horloge: FausseHorloge, dossier_cache: Path | None = None
) -> Outils:
    return construire_outils(transport, horloge, dossier_cache)
