"""Résolution des désignations : du texte libre aux entités du domaine.

Déterministe : à texte et données égaux (calendrier, date, pilotes), même réponse. Quand la désignation
est ambiguë ou introuvable, elle renvoie les candidats plutôt qu'un choix arbitraire.
"""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from chatbot_wrc.source_wrc import Calendrier, Rallye, Speciale, Speciales, Statut

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


@dataclass(frozen=True)
class ResolutionSpeciale:
    # La spéciale désignée, si elle existe.
    speciale: Speciale | None
    # Sinon, les spéciales du rallye.
    candidats: list[Speciale]
    # Vrai pour « la dernière » quand aucune spéciale n'a encore été disputée.
    aucune_disputee: bool = False


def resoudre_speciale(texte: str, speciales: Speciales) -> ResolutionSpeciale:
    """La spéciale désignée par son numéro (« ES7 », « spéciale 7 »), par « la dernière »
    (la dernière disputée) ou par « la Power Stage »."""
    normalise = _normaliser(texte)
    trouvee = None
    if re.search(r"\b(power\s*stage|ps)\b", normalise):
        trouvee = next((s for s in speciales.liste if s.power_stage), None)
    elif re.fullmatch(r"(la |le )?(dernier|derniere)( speciale| es)?( disputee)?", normalise):
        trouvee = speciales.derniere_disputee()
        if trouvee is None:
            return ResolutionSpeciale(None, speciales.liste, aucune_disputee=True)
    # Un chiffre seul dans un nom (« Arganil 2 ») n'est pas un numéro de spéciale.
    elif numero := re.search(r"(?:^|\b(?:es|ss|speciale)\s*)(\d+)\b", normalise):
        trouvee = next((s for s in speciales.liste if s.numero == int(numero[1])), None)
    return ResolutionSpeciale(trouvee, [] if trouvee else speciales.liste)


# Les surnoms courants des pilotes, avec le nom complet qu'ils désignent.
_SURNOMS = {
    "seb": "sebastien ogier",
    "taka": "takamoto katsuta",
    "jml": "jari matti latvala",
    "olly": "oliver solberg",
    "elf": "elfyn evans",
}

# Le nombre de noms proches proposés quand un pilote est introuvable.
_PROPOSITIONS = 5


@dataclass(frozen=True)
class ResolutionPilote:
    # Le nom du pilote désigné, s'il n'y en a qu'un.
    pilote: str | None
    # Sinon, les pilotes parmi lesquels choisir.
    candidats: list[str]


def resoudre_pilote(texte: str, pilotes: list[str]) -> ResolutionPilote:
    """Le pilote désigné par son prénom, son nom ou un surnom courant, parmi les noms
    complets donnés.

    Chaque mot du texte doit désigner un mot du nom, exactement ou, à défaut, à une
    faute de frappe près. Introuvable, il renvoie les noms les plus proches.
    """
    mots = {m for mot in _normaliser(texte).split() for m in _SURNOMS.get(mot, mot).split()}
    noms = {p: _normaliser(p).split() for p in pilotes}
    for correspond in (_egal, _proche):
        trouves = [
            p for p, mots_du_nom in noms.items()
            if mots and all(any(correspond(m, n) for n in mots_du_nom) for m in mots)
        ]
        if len(trouves) == 1:
            return ResolutionPilote(trouves[0], [])
        if trouves:
            return ResolutionPilote(None, trouves)
    ecart = {
        p: sum(min(_distance(m, n) for n in mots_du_nom) for m in mots)
        for p, mots_du_nom in noms.items()
    }
    return ResolutionPilote(None, sorted(pilotes, key=lambda p: ecart[p])[:_PROPOSITIONS])


def _egal(mot: str, mot_du_nom: str) -> bool:
    return mot == mot_du_nom


def _proche(mot: str, mot_du_nom: str) -> bool:
    """Une faute de frappe légère : une lettre en trop, en moins, changée ou deux
    lettres inversées (deux fautes pour un mot long). Pas de faute sur un mot court."""
    tolerance = 0 if len(mot) < 4 else 1 if len(mot) < 8 else 2
    return _distance(mot, mot_du_nom) <= tolerance


def _distance(a: str, b: str) -> int:
    """La distance de Damerau-Levenshtein restreinte (une transposition compte pour un)."""
    d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(
                d[i - 1][j] + 1,
                d[i][j - 1] + 1,
                d[i - 1][j - 1] + (a[i - 1] != b[j - 1]),
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def meme_nom(a: str, b: str) -> bool:
    """Vrai si les deux noms ne diffèrent que par les accents, la casse ou la ponctuation."""
    return _normaliser(a) == _normaliser(b)


def _normaliser(texte: str) -> str:
    """Le texte en mots séparés d'une espace, sans accents ni majuscules ni ponctuation."""
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", sans_accents.lower()))
