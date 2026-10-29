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
from chatbot_wrc.resolution import meme_nom, resoudre_pilote, resoudre_rallye
from chatbot_wrc.source_wrc import (
    CHAMPIONNATS,
    Categorie,
    ClassementChampionnat,
    DonneeIndisponible,
    Fraicheur,
    LigneChampionnat,
    Rallye,
    Saison,
    SourceWRC,
    TypeChampionnat,
)
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
    {
        "name": "classement_championnat",
        "description": (
            "Le classement du championnat de la saison en cours du WRC, pour une catégorie "
            "(WRC1 ou WRC2) et un type (pilotes, copilotes, ou constructeurs en WRC1 "
            "seulement). Pour chaque position : le nom, la nationalité, le constructeur, "
            "l'équipe, les points totaux, l'écart de points au leader et au précédent, et "
            "les points rallye par rallye (seuls les rallyes disputés sont listés). Pour "
            "chaque rallye : le statut (classé, abandon…), la position à l'arrivée (pilotes et "
            "copilotes classés), les "
            "points, leur détail tel que publié (« 25 + 5 + 4 ») et, pour les pilotes et "
            "copilotes, ce détail nommé : classement final, dimanche, Power Stage (un terme "
            "absent veut dire aucun point). Pour un constructeur, le détail additionne les "
            "points de ses équipages qui marquent. `compte` est faux pour un résultat "
            "décompté (seuls les meilleurs résultats comptent en WRC2). Le résultat dit aussi "
            "après quel rallye date le classement, la fraîcheur et l'indicateur de donnée "
            "périmée. Juste après le passage à une nouvelle saison, le classement de la "
            "saison qui vient de se terminer est aussi renvoyé (`saison_terminee`). À "
            "utiliser pour toute question sur le classement du championnat, les points ou "
            "les écarts de points."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "categorie": {"type": "string", "enum": ["WRC1", "WRC2"]},
                "type": {"type": "string", "enum": ["pilotes", "copilotes", "constructeurs"]},
            },
            "required": ["categorie", "type"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "engages",
        "description": (
            "Les équipages engagés sur un rallye de la saison en cours du WRC, en WRC1 et "
            "WRC2 (les autres catégories sont filtrées) : pour chacun, le numéro de la "
            "voiture, le pilote, le copilote, la voiture, la catégorie, le constructeur de "
            "la voiture et l'équipe qui l'engage, plus le rallye reconnu, la fraîcheur et "
            "l'indicateur de donnée périmée. Une liste vide veut dire que la source n'a pas "
            "encore publié les engagés. Le rallye se désigne en texte libre, tel que "
            "l'utilisateur l'a dit : nom, pays ou ville (« Portugal », « le Monte-Carlo », "
            "« Sardaigne ») ou repère relatif (« en cours », « dernier », « prochain », "
            "« ce week-end »). Si la désignation est ambiguë ou introuvable, aucun rallye "
            "n'est choisi : `candidats` liste les rallyes possibles."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"rallye": {"type": "string"}},
            "required": ["rallye"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "fiche_pilote",
        "description": (
            "La fiche d'un pilote WRC1 ou WRC2 de la saison en cours du WRC : nom, "
            "nationalité, catégorie, et, d'après les engagés de son dernier rallye disputé "
            "(`dernier_rallye`), sa voiture, son constructeur, son équipe et son copilote "
            "(voiture et copilote valent null si ces engagés ne sont pas disponibles). "
            "`championnats` donne sa position, ses points et son écart au leader dans "
            "chaque classement du championnat des pilotes où il figure : un pilote WRC2 "
            "qui marque des points au classement du championnat WRC1 y figure aussi. Plus la "
            "saison, la fraîcheur et l'indicateur de donnée périmée. Juste après le "
            "passage à une nouvelle saison, tant que personne n'y est classé, la fiche "
            "porte sur la saison qui vient de se terminer. Le pilote se désigne en texte "
            "libre, tel que l'utilisateur l'a dit : prénom, nom ou surnom courant, avec ou "
            "sans accents, même avec une faute de frappe (« Ogier », « Seb », « Thierry »). "
            "Si la désignation est ambiguë, aucun pilote n'est choisi : `candidats` liste "
            "les pilotes possibles. Si le pilote est introuvable, `candidats` liste les "
            "noms les plus proches, qui peuvent n'avoir aucun rapport."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"nom": {"type": "string"}},
            "required": ["nom"],
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
        if nom == "classement_championnat":
            return self.classement_championnat(
                str(arguments.get("categorie", "")), str(arguments.get("type", ""))
            )
        if nom == "engages":
            return self.engages(str(arguments.get("rallye", "")))
        if nom == "fiche_pilote":
            return self.fiche_pilote(str(arguments.get("nom", "")))
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

    def classement_championnat(self, categorie: str, type_: str) -> dict[str, Any]:
        championnat = _championnat(categorie, type_)
        if championnat is None:
            return _requete_invalide(categorie, type_)
        try:
            classements = self._source.classement_championnat(*championnat)
        except DonneeIndisponible:
            return _indisponible("le classement du championnat")
        resultat = _classement_championnat(classements.en_cours)
        if classements.terminee is not None:
            resultat["saison_terminee"] = _classement_championnat(classements.terminee)
        return resultat | _etat_donnee(classements.fraicheur)

    def engages(self, rallye: str) -> dict[str, Any]:
        try:
            calendrier = self._source.calendrier()
        except DonneeIndisponible:
            return _indisponible("le calendrier")
        aujourdhui = self._source.aujourdhui()
        resolution = resoudre_rallye(rallye, calendrier, aujourdhui)
        if resolution.rallye is None:
            return {
                "rallye_non_resolu": rallye,
                "candidats": [_rallye(r, aujourdhui) for r in resolution.candidats],
            } | _etat_donnee(calendrier.fraicheur)
        designe = {"rallye": _rallye(resolution.rallye, aujourdhui)}
        try:
            engages = self._source.engages(resolution.rallye)
        except DonneeIndisponible:
            return designe | _indisponible("les engagés de ce rallye")
        return designe | {
            "equipages": [
                {
                    "numero": e.numero,
                    "pilote": e.pilote,
                    "copilote": e.copilote,
                    "voiture": e.voiture,
                    "categorie": str(e.categorie),
                    "constructeur": e.constructeur,
                    "equipe": e.equipe,
                }
                for e in engages.equipages
            ],
        } | _etat_donnee(Fraicheur.combiner([calendrier.fraicheur, engages.fraicheur]))

    def fiche_pilote(self, nom: str) -> dict[str, Any]:
        try:
            calendrier = self._source.calendrier()
            classements = {
                c: self._source.classement_championnat(c, TypeChampionnat.PILOTES)
                for c in Categorie
            }
        except DonneeIndisponible:
            return _indisponible("le classement du championnat")
        fraicheurs = [calendrier.fraicheur, *(c.fraicheur for c in classements.values())]
        en_cours = {c: cl.en_cours for c, cl in classements.items()}
        if not any(cl.lignes for cl in en_cours.values()):
            # Juste après le basculement, la nouvelle saison n'a encore classé personne.
            en_cours = {
                c: cl.en_cours if cl.terminee is None else cl.terminee
                for c, cl in classements.items()
            }
        lignes = {
            c: {ligne.nom: ligne for ligne in classement.lignes}
            for c, classement in en_cours.items()
        }
        noms = list(dict.fromkeys(n for par_nom in lignes.values() for n in par_nom))
        resolution = resoudre_pilote(nom, noms)
        if resolution.pilote is None:
            return {
                "pilote_non_resolu": nom,
                "candidats": [
                    {"nom": n, "categorie": str(_categorie(n, lignes))}
                    for n in resolution.candidats
                ],
            } | _etat_donnee(Fraicheur.combiner(fraicheurs))
        pilote = resolution.pilote
        ligne = lignes[_categorie(pilote, lignes)][pilote]
        dernier = max(
            (r for par_nom in lignes.values() if pilote in par_nom
             for r in par_nom[pilote].rallyes),
            key=lambda r: r.numero,
            default=None,
        )
        saison = next(iter(en_cours.values())).saison
        rallye = None if dernier is None else next(
            (
                r for s in (calendrier.en_cours, calendrier.terminee)
                if s is not None and s.annee == saison
                for r in s.rallyes if r.numero == dernier.numero
            ),
            None,
        )
        equipage = None
        if rallye is not None:
            try:
                engages = self._source.engages(rallye)
            except DonneeIndisponible:
                pass
            else:
                fraicheurs.append(engages.fraicheur)
                equipage = next(
                    (e for e in engages.equipages if meme_nom(e.pilote, pilote)), None
                )
        return {
            "saison": saison,
            "pilote": {
                "nom": pilote,
                "nationalite": ligne.nationalite,
                # La priorité FIA de son dernier engagement fait foi, sinon ses classements.
                "categorie": str(
                    _categorie(pilote, lignes) if equipage is None else equipage.categorie
                ),
                "voiture": None if equipage is None else equipage.voiture,
                "constructeur": ligne.constructeur if equipage is None else equipage.constructeur,
                "equipe": ligne.equipe if equipage is None else equipage.equipe,
                "copilote": None if equipage is None else equipage.copilote,
                "dernier_rallye": (
                    None if dernier is None
                    else {"numero": dernier.numero, "rallye": dernier.rallye}
                ),
                "championnats": [
                    {
                        "categorie": str(c),
                        "position": par_nom[pilote].position,
                        "points": par_nom[pilote].points,
                        "ecart_au_leader": (
                            en_cours[c].lignes[0].points - par_nom[pilote].points
                        ),
                    }
                    for c, par_nom in lignes.items()
                    if pilote in par_nom
                ],
            },
        } | _etat_donnee(Fraicheur.combiner(fraicheurs))


def _categorie(pilote: str, lignes: dict[Categorie, dict[str, LigneChampionnat]]) -> Categorie:
    """Un pilote classé en WRC2 court en WRC2 ; le championnat du monde des pilotes
    (WRC1) classe aussi les pilotes WRC2 qui y marquent des points."""
    return Categorie.WRC2 if pilote in lignes[Categorie.WRC2] else Categorie.WRC1


def _saison(saison: Saison, aujourdhui: date) -> dict[str, Any]:
    return {
        "saison": saison.annee,
        "rallyes": [
            _rallye_de_la_saison(r, aujourdhui) for r in saison.rallyes
        ],
    }


def _rallye(rallye: Rallye, aujourdhui: date) -> dict[str, Any]:
    return {"saison": rallye.saison, **_rallye_de_la_saison(rallye, aujourdhui)}


def _rallye_de_la_saison(rallye: Rallye, aujourdhui: date) -> dict[str, Any]:
    return {
        "numero": rallye.numero,
        "nom": rallye.nom,
        "pays": rallye.pays,
        "lieu": rallye.lieu,
        "debut": rallye.debut.isoformat(),
        "fin": rallye.fin.isoformat(),
        "statut": str(rallye.statut(aujourdhui)),
    }


def _championnat(categorie: str, type_: str) -> tuple[Categorie, TypeChampionnat] | None:
    try:
        championnat = (Categorie(categorie.strip().upper()), TypeChampionnat(type_.strip().lower()))
    except ValueError:
        return None
    return championnat if championnat in CHAMPIONNATS else None


def _classement_championnat(classement: ClassementChampionnat) -> dict[str, Any]:
    lignes = []
    for i, ligne in enumerate(classement.lignes):
        lignes.append(
            {
                "position": ligne.position,
                "nom": ligne.nom,
                "nationalite": ligne.nationalite,
                "constructeur": ligne.constructeur,
                "equipe": ligne.equipe,
                "points": ligne.points,
                "ecart_au_leader": classement.lignes[0].points - ligne.points,
                "ecart_au_precedent": classement.lignes[max(i - 1, 0)].points - ligne.points,
                "rallyes": [
                    {
                        "numero": r.numero,
                        "rallye": r.rallye,
                        "statut": r.statut,
                        "position_rallye": r.position_rallye,
                        "points": r.points,
                        "detail": r.detail,
                        "points_detailles": r.points_detailles,
                        "compte": r.compte,
                    }
                    for r in ligne.rallyes
                ],
            }
        )
    dernier = classement.dernier_rallye()
    return {
        "saison": classement.saison,
        "championnat_publie": classement.publie,
        "apres_rallye": None if dernier is None else {"numero": dernier[0], "rallye": dernier[1]},
        "classement": lignes,
    }


def _requete_invalide(categorie: str, type_: str) -> dict[str, Any]:
    return {
        "erreur": (
            f"Pas de championnat « {type_} » en « {categorie} ». Les championnats suivis "
            f"sont : pilotes, copilotes et constructeurs en WRC1 ; pilotes et copilotes en WRC2."
        ),
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
