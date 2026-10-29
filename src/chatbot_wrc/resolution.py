"""Résolution des désignations : du texte libre aux entités du domaine.

Déterministe : à texte, calendrier et date égaux, même réponse. Quand la désignation
est ambiguë ou introuvable, elle renvoie les candidats plutôt qu'un choix arbitraire.
"""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from chatbot_wrc.source_wrc import Calendrier, Rallye, Statut

# Les mots qui ne désignent aucun rallye en particulier.
_MOTS_VIDES = frozenset(
    "le la les l du de des d au aux en a un une an annee rallye rally wrc".split()
)

# Les noms français des pays et des régions, que la source publie en anglais.
_NOMS_FRANCAIS = {
    "Monaco": "monte carlo",
    "Sweden": "suede",
    "Croatia": "croatie",
    "Spain": "espagne canaries",
    "Japan": "japon",
    "Greece": "grece acropole",
    "Estonia": "estonie",
    "Finland": "finlande",
    "Chile": "chili",
    "Italy": "italie",
    "Sardinia": "sardaigne",
    "United States of America": "etats unis usa amerique",
    "United Kingdom": "royaume uni ecosse",
    "Saudi Arabia": "arabie saoudite",
}


@dataclass(frozen=True)
class ResolutionRallye:
    # Le rallye désigné, s'il n'y en a qu'un.
    rallye: Rallye | None
    # Sinon, les rallyes parmi lesquels choisir (tous, si rien ne correspond).
    candidats: list[Rallye]


def resoudre_rallye(texte: str, calendrier: Calendrier, aujourdhui: date) -> ResolutionRallye:
    """Le rallye désigné par son nom, son pays, sa ville ou un repère relatif à la date
    du jour (« en cours », « dernier », « prochain », « ce week-end »), dans la saison
    en cours. Un repère se combine avec un nom (« le dernier Monte-Carlo »).

    Juste après le basculement, la saison qui vient de se terminer reste désignable :
    par son année (« le Portugal 2026 »), par un repère, ou pour un rallye absent de la
    saison en cours.
    """
    saisons = [calendrier.en_cours]
    if calendrier.terminee is not None:
        saisons.append(calendrier.terminee)
    normalise = _normaliser(texte)
    repere = next(((e, c) for e, c in _REPERES if re.search(rf"\b{e}\b", normalise)), None)
    if repere is not None:
        normalise = re.sub(rf"\b{repere[0]}\b", " ", normalise)
    mots = set(normalise.split()) - _MOTS_VIDES
    annees = {str(s.annee) for s in saisons} & mots
    if annees:
        saisons = [s for s in saisons if str(s.annee) in annees]
        mots -= annees
    tous = [r for s in saisons for r in s.rallyes]
    if repere is not None:
        parmi = [r for r in tous if mots <= _mots_du_rallye(r)]
        rallye = repere[1](parmi, aujourdhui)
        return ResolutionRallye(rallye, [] if rallye else parmi or tous)
    for saison in saisons if mots else []:
        trouves = [r for r in saison.rallyes if mots <= _mots_du_rallye(r)]
        if trouves:
            return _choisir(trouves)
    return ResolutionRallye(None, tous)


def _en_cours(rallyes: list[Rallye], aujourdhui: date) -> Rallye | None:
    return next((r for r in rallyes if r.statut(aujourdhui) == Statut.EN_COURS), None)


def _dernier(rallyes: list[Rallye], aujourdhui: date) -> Rallye | None:
    passes = [r for r in rallyes if r.statut(aujourdhui) == Statut.PASSE]
    return max(passes, key=lambda r: r.fin, default=None)


def _prochain(rallyes: list[Rallye], aujourdhui: date) -> Rallye | None:
    a_venir = [r for r in rallyes if r.statut(aujourdhui) == Statut.A_VENIR]
    return min(a_venir, key=lambda r: r.debut, default=None)


def _ce_week_end(rallyes: list[Rallye], aujourdhui: date) -> Rallye | None:
    """Le rallye disputé pendant la semaine du jour, du lundi au dimanche."""
    lundi = aujourdhui - timedelta(days=aujourdhui.weekday())
    dimanche = lundi + timedelta(days=6)
    return next((r for r in rallyes if r.debut <= dimanche and r.fin >= lundi), None)


# Les repères relatifs, cherchés dans le texte sans accents ni majuscules.
_REPERES: list[tuple[str, Callable[[list[Rallye], date], Rallye | None]]] = [
    (r"(en cours|actuel|aujourd hui)", _en_cours),
    (r"(dernier|derniere|precedent)", _dernier),
    (r"(prochain|suivant)", _prochain),
    (r"ce (week end|weekend|we)", _ce_week_end),
]


def _choisir(rallyes: list[Rallye]) -> ResolutionRallye:
    if len(rallyes) == 1:
        return ResolutionRallye(rallyes[0], [])
    return ResolutionRallye(None, rallyes)


def _mots_du_rallye(rallye: Rallye) -> set[str]:
    texte = " ".join([rallye.nom, rallye.pays, rallye.lieu])
    francais = [nom for cle, nom in _NOMS_FRANCAIS.items() if cle in texte]
    return set(_normaliser(" ".join([texte, *francais])).split())


def _normaliser(texte: str) -> str:
    """Le texte en mots séparés d'une espace, sans accents ni majuscules ni ponctuation."""
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", sans_accents.lower()))
