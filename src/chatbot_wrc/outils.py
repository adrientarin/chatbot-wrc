"""Les outils exposés à Claude : texte libre en entrée, résultat structuré en sortie.

Chaque résultat contient les données, leur fraîcheur et l'indicateur de donnée
périmée (la source est injoignable ou a changé : c'est la dernière donnée connue).
"""

from datetime import date
from pathlib import Path
from typing import Any

from anthropic.types.beta import BetaToolParam

from chatbot_wrc.cache import Cache
from chatbot_wrc.horloge import Horloge
from chatbot_wrc.source_wrc import DonneeIndisponible, Fraicheur, Saison, SourceWRC
from chatbot_wrc.transport import Transport


DEFINITIONS: list[BetaToolParam] = [
    {
        "name": "calendrier",
        "description": (
            "Le calendrier de la saison en cours du WRC, tel que la source le publie : "
            "chaque rallye avec son numéro dans la saison, son pays, son lieu, ses dates et "
            "son statut (passé, en cours, à venir), plus la date du jour, la fraîcheur de la "
            "donnée et l'indicateur de donnée périmée. Juste après le passage à une nouvelle "
            "saison, la saison qui vient de se terminer est aussi renvoyée. À utiliser pour "
            "toute question sur les dates des rallyes, le prochain, le dernier ou celui en cours."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


class Outils:
    def __init__(self, source: SourceWRC) -> None:
        self._source = source

    def executer(self, nom: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Exécute l'outil demandé par Claude."""
        if nom == "calendrier":
            return self.calendrier()
        raise ValueError(f"outil inconnu : {nom}")

    def calendrier(self) -> dict[str, Any]:
        try:
            calendrier = self._source.calendrier()
        except DonneeIndisponible:
            return _indisponible("le calendrier")
        aujourdhui = self._source.aujourdhui()
        resultat: dict[str, Any] = {
            "aujourd_hui": aujourdhui.isoformat(),
            **_saison(calendrier.en_cours, aujourdhui),
        }
        if calendrier.terminee is not None:
            resultat["saison_terminee"] = _saison(calendrier.terminee, aujourdhui)
        return resultat | _etat_donnee(calendrier.fraicheur)


def _saison(saison: Saison, aujourdhui: date) -> dict[str, Any]:
    return {
        "saison": saison.annee,
        "rallyes": [
            {
                "numero": r.numero,
                "nom": r.nom,
                "pays": r.pays,
                "lieu": r.lieu,
                "debut": r.debut.isoformat(),
                "fin": r.fin.isoformat(),
                "statut": str(r.statut(aujourdhui)),
            }
            for r in saison.rallyes
        ],
    }


def _etat_donnee(fraicheur: Fraicheur) -> dict[str, Any]:
    return {
        "donnee_disponible": True,
        "fraicheur": {"heure_donnee": fraicheur.recupere_le.isoformat(timespec="minutes")},
        "donnee_perimee": fraicheur.perimee,
    }


def _indisponible(quoi: str) -> dict[str, Any]:
    return {
        "donnee_disponible": False,
        "message": (
            f"La source n'a pas fourni de donnée exploitable et aucune donnée n'est connue "
            f"pour {quoi}."
        ),
    }


def construire_outils(
    transport: Transport, horloge: Horloge, dossier_cache: Path | None = None
) -> Outils:
    return Outils(SourceWRC(transport, horloge, Cache(horloge, dossier_cache)))
