"""Cache des réponses de la source, avec leur heure de récupération."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from chatbot_wrc.horloge import Horloge


class ErreurSource(Exception):
    """La source n'a pas fourni de réponse exploitable (panne ou format inattendu)."""


class DonneeIndisponible(Exception):
    """La source est injoignable et aucune donnée n'est connue."""


@dataclass(frozen=True)
class Lecture:
    valeur: Any
    recupere_le: datetime
    perimee: bool


class Cache:
    """Rafraîchi à la demande : la source n'est rappelée qu'à expiration, sans tâche de fond.

    Si la source échoue, la dernière donnée connue est renvoyée, marquée comme périmée.
    Avec un dossier, les réponses y sont aussi écrites et survivent au redémarrage.
    """

    def __init__(self, horloge: Horloge, dossier: Path | None = None) -> None:
        self._horloge = horloge
        self._dossier = dossier
        self._entrees: dict[str, Lecture] = {}

    def obtenir(self, cle: str, recuperer: Callable[[], Any], validite: timedelta) -> Lecture:
        connue = self._entrees.get(cle) or self._relire(cle)
        if connue is not None and self._horloge.maintenant() - connue.recupere_le < validite:
            return connue
        try:
            valeur = recuperer()
        except ErreurSource as erreur:
            if connue is None:
                raise DonneeIndisponible(str(erreur)) from erreur
            return Lecture(connue.valeur, connue.recupere_le, perimee=True)
        lecture = Lecture(valeur, self._horloge.maintenant(), perimee=False)
        self._entrees[cle] = lecture
        self._ecrire(cle, lecture)
        return lecture

    def _fichier(self, cle: str) -> Path | None:
        return None if self._dossier is None else self._dossier / f"{cle}.json"

    def _relire(self, cle: str) -> Lecture | None:
        fichier = self._fichier(cle)
        if fichier is None or not fichier.exists():
            return None
        try:
            contenu = json.loads(fichier.read_text(encoding="utf-8"))
            return Lecture(
                contenu["valeur"], datetime.fromisoformat(contenu["recupere_le"]), perimee=False
            )
        except (ValueError, KeyError, TypeError):
            return None  # fichier abîmé : on fait comme s'il n'existait pas

    def _ecrire(self, cle: str, lecture: Lecture) -> None:
        fichier = self._fichier(cle)
        if fichier is None:
            return
        fichier.parent.mkdir(parents=True, exist_ok=True)
        contenu = {"recupere_le": lecture.recupere_le.isoformat(), "valeur": lecture.valeur}
        fichier.write_text(json.dumps(contenu, ensure_ascii=False), encoding="utf-8")
