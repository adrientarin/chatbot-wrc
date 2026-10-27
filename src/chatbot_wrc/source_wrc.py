"""Module source WRC : le seul à connaître l'API de wrc.com (voir ADR 0001).

Il expose des objets du domaine et masque les adresses, les identifiants et le
format JSON de l'API.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any

from chatbot_wrc.cache import Cache, DonneeIndisponible, ErreurSource, Lecture
from chatbot_wrc.horloge import Horloge
from chatbot_wrc.transport import ErreurTransport, Transport

ADRESSE_API = "https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api"
NOM_CHAMPIONNAT = "World Rally Championship"
VALIDITE_LONGUE = timedelta(hours=24)

__all__ = ["Calendrier", "DonneeIndisponible", "Fraicheur", "Rallye", "Saison", "SourceWRC", "Statut"]


class Statut(StrEnum):
    PASSE = "passé"
    EN_COURS = "en cours"
    A_VENIR = "à venir"


@dataclass(frozen=True)
class Rallye:
    numero: int
    nom: str
    pays: str
    lieu: str
    debut: date
    fin: date

    def statut(self, aujourdhui: date) -> Statut:
        if aujourdhui < self.debut:
            return Statut.A_VENIR
        if aujourdhui > self.fin:
            return Statut.PASSE
        return Statut.EN_COURS


@dataclass(frozen=True)
class Fraicheur:
    recupere_le: datetime
    perimee: bool

    @staticmethod
    def combiner(lectures: list[Lecture]) -> "Fraicheur":
        """Une donnée construite à partir de plusieurs réponses a l'âge de la plus ancienne."""
        return Fraicheur(
            recupere_le=min(l.recupere_le for l in lectures),
            perimee=any(l.perimee for l in lectures),
        )


@dataclass(frozen=True)
class Saison:
    annee: int
    rallyes: list[Rallye]


@dataclass(frozen=True)
class Calendrier:
    en_cours: Saison
    # La saison qui vient de se terminer, juste après le basculement sur la suivante.
    terminee: Saison | None
    fraicheur: Fraicheur


class SourceWRC:
    def __init__(self, transport: Transport, horloge: Horloge, cache: Cache) -> None:
        self._transport = transport
        self._horloge = horloge
        self._cache = cache

    def aujourdhui(self) -> date:
        return self._horloge.maintenant().date()

    def calendrier(self) -> Calendrier:
        """Le calendrier de la saison en cours, tel que la source le publie.

        La saison en cours est celle de l'année civile. Tant que son calendrier
        n'est pas publié, c'est la précédente. Une fois tous ses rallyes passés,
        elle cède la place à la suivante dès que celle-ci est publiée.
        """
        lecture_saisons = self._lire("seasons", "seasons.json", _lire_saisons)
        saisons: dict[int, int] = _lire_saisons(lecture_saisons.valeur)
        lectures = [lecture_saisons]
        aujourdhui = self.aujourdhui()

        def publiee(annee: int) -> list[Rallye]:
            if annee not in saisons:
                return []
            lecture = self._lire_saison(saisons[annee])
            lectures.append(lecture)
            return _lire_rallyes(lecture.valeur)

        annee = aujourdhui.year
        en_cours = Saison(annee, publiee(annee))
        terminee = None
        if not en_cours.rallyes:
            en_cours = Saison(annee - 1, publiee(annee - 1))
        elif all(r.statut(aujourdhui) == Statut.PASSE for r in en_cours.rallyes):
            suivante = Saison(annee + 1, publiee(annee + 1))
            if suivante.rallyes:
                en_cours, terminee = suivante, en_cours
        return Calendrier(en_cours, terminee, Fraicheur.combiner(lectures))

    def _lire_saison(self, id_saison: int) -> Lecture:
        return self._lire(
            f"season-detail-{id_saison}",
            f"season-detail.json?seasonId={id_saison}",
            _lire_rallyes,
        )

    def _lire(self, cle: str, chemin: str, valider: Callable[[Any], object]) -> Lecture:
        def recuperer() -> Any:
            try:
                valeur = json.loads(self._transport.get(f"{ADRESSE_API}/{chemin}"))
                valider(valeur)
            except ErreurTransport as erreur:
                raise ErreurSource(str(erreur)) from erreur
            except (ValueError, KeyError, TypeError) as erreur:
                raise ErreurSource(f"format inattendu pour {chemin} : {erreur!r}") from erreur
            return valeur

        return self._cache.obtenir(cle, recuperer, VALIDITE_LONGUE)


def _lire_saisons(brut: Any) -> dict[int, int]:
    """Année -> identifiant de la saison du championnat du monde."""
    return {
        int(s["year"]): int(s["seasonId"]) for s in brut if s["name"] == NOM_CHAMPIONNAT
    }


def _lire_rallyes(brut: Any) -> list[Rallye]:
    rallyes = []
    for manche_api in brut["seasonRounds"]:
        evenement = manche_api["event"]
        rallyes.append(
            Rallye(
                numero=int(manche_api["order"]),
                nom=evenement["name"],
                pays=evenement["country"]["name"],
                lieu=evenement["location"],
                debut=date.fromisoformat(evenement["startDate"]),
                fin=date.fromisoformat(evenement["finishDate"]),
            )
        )
    return sorted(rallyes, key=lambda r: r.numero)
