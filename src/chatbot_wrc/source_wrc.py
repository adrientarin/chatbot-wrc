"""Module source WRC : le seul à connaître l'API de wrc.com (voir ADR 0001).

Il expose des objets du domaine et masque les adresses, les identifiants et le
format JSON de l'API.
"""

import json
import re
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import Any

from chatbot_wrc.cache import Cache, DonneeIndisponible, ErreurSource, Lecture
from chatbot_wrc.horloge import Horloge
from chatbot_wrc.transport import ErreurTransport, Transport

ADRESSE_API = "https://p-p.redbull.com/rb-wrccom-lintegration-yv-prod/api"
NOM_CHAMPIONNAT = "World Rally Championship"
VALIDITE_LONGUE = timedelta(hours=24)
VALIDITE_COURTE = timedelta(minutes=1)

__all__ = [
    "Abandon",
    "CHAMPIONNATS",
    "Calendrier",
    "Categorie",
    "ClassementChampionnat",
    "ClassementRallye",
    "ClassementsChampionnat",
    "DonneeIndisponible",
    "Engages",
    "Equipage",
    "Fraicheur",
    "LigneChampionnat",
    "LigneRallye",
    "PointsRallye",
    "Rallye",
    "Saison",
    "SourceWRC",
    "Speciale",
    "Speciales",
    "Statut",
    "TempsEquipage",
    "TempsSpeciale",
    "TypeChampionnat",
]


class Categorie(StrEnum):
    WRC1 = "WRC1"
    WRC2 = "WRC2"


class TypeChampionnat(StrEnum):
    PILOTES = "pilotes"
    COPILOTES = "copilotes"
    CONSTRUCTEURS = "constructeurs"


# Les seuls championnats retenus (le championnat des équipes et les autres catégories
# sont ignorés), avec leur nom dans la source.
_NOMS_CHAMPIONNATS = {
    (Categorie.WRC1, TypeChampionnat.PILOTES): "FIA World Rally Championship for Drivers",
    (Categorie.WRC1, TypeChampionnat.COPILOTES): "FIA World Rally Championship for Co-Drivers",
    (Categorie.WRC1, TypeChampionnat.CONSTRUCTEURS): (
        "FIA World Rally Championship for Manufacturers"
    ),
    (Categorie.WRC2, TypeChampionnat.PILOTES): "FIA WRC2 Championship for Drivers",
    (Categorie.WRC2, TypeChampionnat.COPILOTES): "FIA WRC2 Championship for Co-Drivers",
}
CHAMPIONNATS = frozenset(_NOMS_CHAMPIONNATS)


class Statut(StrEnum):
    PASSE = "passé"
    EN_COURS = "en cours"
    A_VENIR = "à venir"


@dataclass(frozen=True)
class Rallye:
    saison: int
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
    def combiner(lectures: "Sequence[Lecture | Fraicheur]") -> "Fraicheur":
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


@dataclass(frozen=True)
class Equipage:
    numero: str
    pilote: str
    copilote: str | None
    voiture: str
    categorie: Categorie
    constructeur: str | None
    equipe: str | None


@dataclass(frozen=True)
class Engages:
    equipages: list[Equipage]
    fraicheur: Fraicheur


@dataclass(frozen=True)
class PointsRallye:
    numero: int
    rallye: str
    statut: str
    # La position à l'arrivée du rallye, pour un pilote ou un copilote classé.
    position_rallye: str | None
    points: int
    # Le détail tel que la source le publie, par exemple « 25 + 5 + 4 ».
    detail: str | None
    # Le même détail, nommé (pilotes et copilotes seulement) : classement final,
    # dimanche, Power Stage. Un terme absent n'a pas été publié (pas de points).
    points_detailles: dict[str, int] | None
    # Faux si ce résultat est décompté (seuls les meilleurs résultats comptent en WRC2).
    compte: bool


@dataclass(frozen=True)
class LigneChampionnat:
    position: int
    nom: str
    nationalite: str | None
    constructeur: str
    equipe: str | None
    points: int
    rallyes: list[PointsRallye]


@dataclass(frozen=True)
class ClassementChampionnat:
    saison: int
    # Faux tant que la source n'a pas créé ce championnat pour la saison.
    publie: bool
    lignes: list[LigneChampionnat]

    def dernier_rallye(self) -> tuple[int, str] | None:
        """Le dernier rallye (numéro, nom) pris en compte, s'il y en a un."""
        return max(
            ((r.numero, r.rallye) for l in self.lignes for r in l.rallyes), default=None
        )


@dataclass(frozen=True)
class ClassementsChampionnat:
    en_cours: ClassementChampionnat
    # Celui de la saison qui vient de se terminer, juste après le basculement.
    terminee: ClassementChampionnat | None
    fraicheur: Fraicheur


def _code_speciale(numero: int) -> str:
    return f"ES{numero}"


@dataclass(frozen=True)
class Speciale:
    numero: int
    nom: str
    distance_km: float
    power_stage: bool
    statut: str
    # Le nombre de décimales du chronométrage (trois en Power Stage).
    decimales: int

    @property
    def code(self) -> str:
        return _code_speciale(self.numero)

    @property
    def disputee(self) -> bool:
        return self.statut in _STATUTS_SPECIALES.values()


@dataclass(frozen=True)
class Speciales:
    liste: list[Speciale]
    fraicheur: Fraicheur

    def derniere_disputee(self) -> Speciale | None:
        return max((s for s in self.liste if s.disputee), key=lambda s: s.numero, default=None)


@dataclass(frozen=True)
class TempsEquipage:
    equipage: Equipage
    # Sans temps pour un équipage qui n'a pas terminé la spéciale.
    temps_ms: int | None
    # « non partant » ou « abandon » pour un équipage sans temps.
    statut: str | None
    # D'où vient un temps qui n'a pas été réalisé sur la route (forfaitaire…).
    nature: str | None


@dataclass(frozen=True)
class TempsSpeciale:
    temps: list[TempsEquipage]
    fraicheur: Fraicheur


@dataclass(frozen=True)
class LigneRallye:
    equipage: Equipage
    # Le cumul des temps, pénalités incluses.
    temps_ms: int
    penalite_ms: int
    # Le code de la spéciale de l'abandon d'un équipage reparti en Super Rally.
    super_rally_depuis: str | None


@dataclass(frozen=True)
class Abandon:
    equipage: Equipage
    # Le code de la spéciale de rattachement : celle du contrôle où l'équipage s'est
    # arrêté, ou la précédente pour un contrôle hors spéciale (aucune avant la première).
    speciale: str | None
    controle: str | None
    # Le motif tel que la source le publie, en anglais.
    motif: str
    # Vrai si l'équipage peut encore repartir en Super Rally.
    peut_repartir: bool


@dataclass(frozen=True)
class ClassementRallye:
    lignes: list[LigneRallye]
    abandons: list[Abandon]
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
        lecture_saisons = self._lire_liste_saisons()
        saisons = _lire_saisons(lecture_saisons.valeur)
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
        elif all(r.statut(aujourdhui) == Statut.A_VENIR for r in en_cours.rallyes):
            # En janvier, avant le premier rallye, la saison précédente reste connue.
            precedente = Saison(annee - 1, publiee(annee - 1))
            terminee = precedente if precedente.rallyes else None
        return Calendrier(en_cours, terminee, Fraicheur.combiner(lectures))

    def classement_championnat(
        self, categorie: Categorie, type_: TypeChampionnat
    ) -> ClassementsChampionnat:
        """Le classement du championnat de la saison en cours (voir `calendrier`).

        Juste après le basculement, celui de la saison qui vient de se terminer suit.
        """
        calendrier = self.calendrier()
        saisons = _lire_saisons(self._lire_liste_saisons().valeur)
        nom = _NOMS_CHAMPIONNATS[(categorie, type_)]
        lectures: list[Lecture | Fraicheur] = [calendrier.fraicheur]

        def classement(annee: int) -> ClassementChampionnat:
            id_saison = saisons[annee]
            lecture_saison = self._lire_saison(id_saison)
            lectures.append(lecture_saison)
            championnats = _lire_championnats(lecture_saison.valeur)
            if nom not in championnats:
                return ClassementChampionnat(annee, publie=False, lignes=[])
            requete = f"championshipId={championnats[nom]}&seasonId={id_saison}"
            detail = self._lire(
                f"championship-detail-{championnats[nom]}",
                f"championship-detail.json?{requete}",
                _lire_detail_championnat,
            )
            resultats = self._lire(
                f"championship-overall-results-{championnats[nom]}",
                f"championship-overall-results.json?{requete}",
                _lire_resultats,
            )
            lectures.extend([detail, resultats])
            return ClassementChampionnat(
                annee,
                publie=True,
                lignes=_assembler(
                    _lire_detail_championnat(detail.valeur),
                    _lire_resultats(resultats.valeur),
                    detailler=type_ != TypeChampionnat.CONSTRUCTEURS,
                ),
            )

        en_cours = classement(calendrier.en_cours.annee)
        terminee = None if calendrier.terminee is None else classement(calendrier.terminee.annee)
        return ClassementsChampionnat(en_cours, terminee, Fraicheur.combiner(lectures))

    def engages(self, rallye: Rallye) -> Engages:
        """Les équipages engagés en WRC1 et WRC2 sur un rallye du calendrier."""
        evenement = self._evenement(rallye)
        engages = self._lire_engages(evenement)
        return Engages(
            list(_lire_equipages(engages.valeur).values()),
            Fraicheur.combiner([*evenement.lectures, engages]),
        )

    def speciales(self, rallye: Rallye) -> Speciales:
        """Les spéciales d'un rallye du calendrier, dans l'ordre (vide avant leur publication)."""
        lecture = self._speciales_du_rallye(rallye, self._evenement(rallye))
        return Speciales(_lire_speciales(lecture.valeur), Fraicheur.combiner([lecture]))

    def temps_speciale(self, rallye: Rallye, numero: int) -> TempsSpeciale:
        """Les temps d'une spéciale, pour les équipages engagés en WRC1 et WRC2.

        La fraîcheur est celle des temps et des spéciales : les engagés et le calendrier,
        gardés bien plus longtemps, ne disent rien de l'âge du résultat.
        """
        evenement = self._evenement(rallye)
        speciales = self._speciales_du_rallye(rallye, evenement)
        id_speciale = _lire_ids_speciales(speciales.valeur)[numero]
        lecture = self._lire_en_direct(
            rallye,
            f"stagetimes-{evenement.id}-{id_speciale}",
            f"events/{evenement.id}/stages/{id_speciale}/stagetimes.json?rallyId={evenement.id_rallye}",
            _lire_temps,
        )
        equipages = _lire_equipages(self._lire_engages(evenement).valeur)
        return TempsSpeciale(
            [
                TempsEquipage(equipages[t.id_engage], t.temps_ms, t.statut, t.nature)
                for t in _lire_temps(lecture.valeur)
                if t.id_engage in equipages
            ],
            Fraicheur.combiner([speciales, lecture]),
        )

    def classement_rallye(self, rallye: Rallye, numero: int) -> ClassementRallye:
        """Le classement du rallye après une spéciale, pour les équipages WRC1 et WRC2.

        L'état de chaque équipage se lit dans la chronologie des abandons, pas dans les
        résultats : ceux d'une spéciale passée contiennent aussi les équipages qui
        repartiront plus tard en Super Rally. Comme pour `temps_speciale`, la fraîcheur
        est celle des données du rallye.
        """
        evenement = self._evenement(rallye)
        speciales = self._speciales_du_rallye(rallye, evenement)
        ids_speciales = _lire_ids_speciales(speciales.valeur)
        id_speciale = ids_speciales[numero]
        resultats = self._lire_en_direct(
            rallye,
            f"results-{evenement.id}-{id_speciale}",
            f"events/{evenement.id}/stages/{id_speciale}/results.json?rallyId={evenement.id_rallye}",
            _lire_cumuls,
        )
        retraits = self._lire_en_direct(
            rallye,
            f"retirements-{evenement.id}",
            f"events/{evenement.id}/retirements.json",
            _lire_retraits,
        )
        itineraire = self._lire(
            f"itinerary-{evenement.id}-{evenement.id_itineraire}",
            f"events/{evenement.id}/itineraries/{evenement.id_itineraire}.json",
            _lire_controles,
        )
        equipages = _lire_equipages(self._lire_engages(evenement).valeur)
        controles = _rattacher(
            _lire_controles(itineraire.valeur), {i: n for n, i in ids_speciales.items()}
        )
        # Sur la dernière spéciale disputée, tout ce que la source a noté a déjà eu lieu,
        # y compris un abandon au contrôle de la spéciale suivante.
        derniere = not any(
            s.disputee and s.numero > numero for s in _lire_speciales(speciales.valeur)
        )
        situations = _situations(_lire_retraits(retraits.valeur), controles, numero, derniere)
        en_cours = rallye.statut(self.aujourdhui()) == Statut.EN_COURS
        return ClassementRallye(
            [
                LigneRallye(
                    equipages[c.id_engage],
                    c.temps_ms,
                    c.penalite_ms,
                    situations[c.id_engage].super_rally_depuis(controles),
                )
                for c in _lire_cumuls(resultats.valeur)
                if c.id_engage in equipages and not situations[c.id_engage].arret
            ],
            [
                _abandon(arret, equipages[arret[0].id_engage], controles, en_cours)
                for arret in sorted(
                    (s.arret for s in situations.values() if s.arret), key=lambda a: a[0].id
                )
                if arret[0].id_engage in equipages
            ],
            Fraicheur.combiner([speciales, resultats, retraits]),
        )

    def _evenement(self, rallye: Rallye) -> "_Evenement":
        """Les identifiants de l'événement et de son rallye principal, et leurs lectures."""
        saisons = _lire_saisons(self._lire_liste_saisons().valeur)
        lecture_saison = self._lire_saison(saisons[rallye.saison])
        id_evenement = _lire_evenements(lecture_saison.valeur)[rallye.numero]
        evenement = self._lire(
            f"event-{id_evenement}", f"events/{id_evenement}.json", _lire_rallye_principal
        )
        return _Evenement(
            id_evenement,
            *_lire_rallye_principal(evenement.valeur),
            [lecture_saison, evenement],
        )

    def _lire_engages(self, evenement: "_Evenement") -> Lecture:
        return self._lire(
            f"entries-{evenement.id}-{evenement.id_rallye}",
            f"events/{evenement.id}/rallies/{evenement.id_rallye}/entries.json",
            _lire_equipages,
        )

    def _speciales_du_rallye(self, rallye: Rallye, evenement: "_Evenement") -> Lecture:
        return self._lire_en_direct(
            rallye, f"stages-{evenement.id}", f"events/{evenement.id}/stages.json", _lire_speciales
        )

    def _lire_liste_saisons(self) -> Lecture:
        return self._lire("seasons", "seasons.json", _lire_saisons)

    def _lire_saison(self, id_saison: int) -> Lecture:
        return self._lire(
            f"season-detail-{id_saison}",
            f"season-detail.json?seasonId={id_saison}",
            lambda brut: (_lire_rallyes(brut), _lire_championnats(brut)),
        )

    def _lire_en_direct(
        self, rallye: Rallye, cle: str, chemin: str, valider: Callable[[Any], object]
    ) -> Lecture:
        """Une donnée qui évolue pendant le rallye : gardée 1 minute tant qu'il est en
        cours. Une fois le rallye terminé, une réponse lue pendant qu'il se disputait
        peut être incomplète : elle n'est pas reprise, même récente."""
        maintenant = self._horloge.maintenant()
        statut = rallye.statut(maintenant.date())
        if statut == Statut.EN_COURS:
            return self._lire(cle, chemin, valider, VALIDITE_COURTE)
        if statut == Statut.PASSE:
            lendemain = rallye.fin + timedelta(days=1)
            pas_avant = datetime.combine(lendemain, time(), maintenant.tzinfo)
            return self._lire(cle, chemin, valider, pas_avant=pas_avant)
        return self._lire(cle, chemin, valider)

    def _lire(
        self,
        cle: str,
        chemin: str,
        valider: Callable[[Any], object],
        validite: timedelta = VALIDITE_LONGUE,
        pas_avant: datetime | None = None,
    ) -> Lecture:
        def recuperer() -> Any:
            try:
                valeur = json.loads(self._transport.get(f"{ADRESSE_API}/{chemin}"))
                valider(valeur)
            except ErreurTransport as erreur:
                raise ErreurSource(str(erreur)) from erreur
            except (ValueError, KeyError, TypeError) as erreur:
                raise ErreurSource(f"format inattendu pour {chemin} : {erreur!r}") from erreur
            return valeur

        return self._cache.obtenir(cle, recuperer, validite, pas_avant)


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
                saison=int(brut["year"]),
                numero=int(manche_api["order"]),
                nom=evenement["name"],
                pays=evenement["country"]["name"],
                lieu=evenement["location"],
                debut=date.fromisoformat(evenement["startDate"]),
                fin=date.fromisoformat(evenement["finishDate"]),
            )
        )
    return sorted(rallyes, key=lambda r: r.numero)


def _lire_evenements(brut: Any) -> dict[int, int]:
    """Numéro du rallye dans la saison -> identifiant de l'événement dans l'API."""
    return {int(m["order"]): int(m["eventId"]) for m in brut["seasonRounds"]}


@dataclass(frozen=True)
class _Evenement:
    id: int
    id_rallye: int
    id_itineraire: int
    lectures: list[Lecture]


def _lire_rallye_principal(brut: Any) -> tuple[int, int]:
    """Un événement de l'API (« event ») contient un ou plusieurs « rallies » ; seul le
    principal correspond à notre rallye. Renvoie ses identifiants et ceux de son itinéraire."""
    principaux = [
        (int(r["rallyId"]), int(r["itineraryId"])) for r in brut["rallies"] if r["isMain"]
    ]
    if len(principaux) != 1:
        raise ValueError(f"{len(principaux)} rallyes principaux")
    return principaux[0]


# La catégorie d'un engagé se lit dans sa priorité FIA : P1 pour les voitures Rally1
# (WRC1), P2 pour les voitures Rally2 inscrites en WRC2. Les autres (Rally2 sans
# priorité, Rally3 et au-delà) ne sont pas suivis.
_CATEGORIES_ENGAGES = {"P1": Categorie.WRC1, "P2": Categorie.WRC2}


def _lire_equipages(brut: Any) -> dict[int, Equipage]:
    """Identifiant de l'engagé -> équipage, dans l'ordre de la liste des engagés."""
    equipages = {}
    for engage in sorted(brut, key=lambda e: int(e["entryListOrder"])):
        categorie = _CATEGORIES_ENGAGES.get(engage["priority"])
        if categorie is None:
            continue
        copilote = engage["codriver"]
        constructeur = engage["manufacturer"]
        equipe = engage["entrant"]
        equipages[int(engage["entryId"])] = Equipage(
            numero=engage["identifier"],
            pilote=engage["driver"]["fullName"],
            copilote=None if copilote is None else copilote["fullName"],
            voiture=engage["vehicleModel"],
            categorie=categorie,
            constructeur=None if constructeur is None else constructeur["name"],
            equipe=None if equipe is None else equipe["name"],
        )
    return equipages


# Les statuts d'une spéciale disputée. Ceux d'une spéciale à venir ou en cours n'ont pas
# pu être observés (aucun rallye en cours à l'implémentation) : ils sont repris tels quels.
_STATUTS_SPECIALES = {"Completed": "terminée", "Interrupted": "interrompue"}
_DECIMALES = {"Tenth": 1, "Hundredth": 2, "Thousandth": 3}


def _lire_speciales(brut: Any) -> list[Speciale]:
    speciales = [
        Speciale(
            numero=int(s["number"]),
            nom=s["name"],
            distance_km=float(s["distance"]),
            power_stage=s["stageType"] == "PowerStage",
            statut=_STATUTS_SPECIALES.get(s["status"], s["status"]),
            decimales=_DECIMALES.get(s["timingPrecision"], 1),
        )
        for s in brut
    ]
    return sorted(speciales, key=lambda s: s.numero)


def _lire_ids_speciales(brut: Any) -> dict[int, int]:
    """Numéro de la spéciale dans le rallye -> identifiant dans l'API."""
    return {int(s["number"]): int(s["stageId"]) for s in brut}


@dataclass(frozen=True)
class _Temps:
    id_engage: int
    temps_ms: int | None
    statut: str | None
    nature: str | None


_STATUTS_TEMPS = {"DNS": "non partant", "DNF": "abandon"}
# L'origine d'un temps non réalisé sur la route : temps forfaitaire d'une spéciale
# interrompue, temps attribué par les commissaires, temps d'un équipage reparti en
# Super Rally (« Rally2 » dans la source).
_NATURES_TEMPS = {
    "Notional": "forfaitaire",
    "Assessed": "attribué",
    "Rally2": "Super Rally",
}


def _lire_temps(brut: Any) -> list[_Temps]:
    return [
        _Temps(
            id_engage=int(t["entryId"]),
            temps_ms=None if t["elapsedDurationMs"] is None else int(t["elapsedDurationMs"]),
            statut=_STATUTS_TEMPS.get(t["status"]),
            nature=_NATURES_TEMPS.get(t["source"]),
        )
        for t in brut
    ]


@dataclass(frozen=True)
class _Cumul:
    id_engage: int
    temps_ms: int
    penalite_ms: int


def _lire_cumuls(brut: Any) -> list[_Cumul]:
    return [
        _Cumul(int(c["entryId"]), int(c["totalTimeMs"]), int(c["penaltyTimeMs"])) for c in brut
    ]


@dataclass(frozen=True)
class _Retrait:
    id: int
    id_engage: int
    id_controle: int
    motif: str
    statut: str


# Le statut d'une ligne des abandons : « Temporary » (l'équipage peut repartir en Super
# Rally), « Permanent », et « Rejoined » pour la ligne qui note son retour.
_ABANDON_PROVISOIRE = "Temporary"
_REPARTI = "Rejoined"


def _lire_retraits(brut: Any) -> list[_Retrait]:
    return [
        _Retrait(
            id=int(r["retirementId"]),
            id_engage=int(r["entryId"]),
            id_controle=int(r["controlId"]),
            motif=r["reason"],
            statut=r["status"],
        )
        for r in brut
    ]


@dataclass(frozen=True)
class _Controle:
    id: int
    code: str
    id_speciale: int | None


def _lire_controles(brut: Any) -> list[_Controle]:
    """Tous les contrôles de l'itinéraire, dans l'ordre du rallye. La liste des spéciales
    ne donne que les leurs : pas les regroupements ni les assistances."""
    return [
        _Controle(
            int(c["controlId"]),
            c["code"],
            None if c["stageId"] is None else int(c["stageId"]),
        )
        for etape in sorted(brut["itineraryLegs"], key=lambda e: int(e["order"]))
        for section in sorted(etape["itinerarySections"], key=lambda s: int(s["order"]))
        for c in section["controls"]
    ]


@dataclass(frozen=True)
class _Rattachement:
    # La spéciale du contrôle, ou celle qui le précède pour un contrôle hors spéciale.
    speciale: int | None
    controle: str | None


# Un contrôle absent de l'itinéraire : rien ne le situe.
_HORS_ITINERAIRE = _Rattachement(None, None)


def _rattacher(
    controles: list[_Controle], numeros: dict[int, int]
) -> dict[int, _Rattachement]:
    rattaches = {}
    speciale = None
    for controle in controles:
        if controle.id_speciale is not None:
            speciale = numeros.get(controle.id_speciale, speciale)
        rattaches[controle.id] = _Rattachement(speciale, controle.code)
    return rattaches


@dataclass
class _Situation:
    """Où en est un équipage après une spéciale."""

    # Les lignes de l'arrêt en cours ; vide si l'équipage court.
    arret: list[_Retrait] = field(default_factory=list)
    # La première ligne du dernier arrêt dont il est reparti.
    repris: _Retrait | None = None

    def super_rally_depuis(self, controles: dict[int, _Rattachement]) -> str | None:
        if self.repris is None:
            return None
        speciale = controles.get(self.repris.id_controle, _HORS_ITINERAIRE).speciale
        return None if speciale is None else _code_speciale(speciale)


def _situations(
    retraits: list[_Retrait],
    controles: dict[int, _Rattachement],
    numero: int,
    derniere: bool,
) -> defaultdict[int, _Situation]:
    """Par engagé, sa situation après la spéciale `numero`. Un contrôle inconnu compte
    comme déjà passé. `derniere` dit si c'est la dernière spéciale disputée."""
    situations: defaultdict[int, _Situation] = defaultdict(_Situation)
    for retrait in sorted(retraits, key=lambda r: r.id):
        situation = situations[retrait.id_engage]
        speciale = controles.get(retrait.id_controle, _HORS_ITINERAIRE).speciale
        if retrait.statut == _REPARTI:
            # Le retour se note en fin d'étape : il prend effet à la spéciale suivante.
            if situation.arret and (speciale is None or speciale < numero):
                situation.repris, situation.arret = situation.arret[0], []
        elif speciale is None or speciale <= numero or derniere:
            situation.arret.append(retrait)
    return situations


def _abandon(
    arret: list[_Retrait],
    equipage: Equipage,
    controles: dict[int, _Rattachement],
    rallye_en_cours: bool,
) -> Abandon:
    """L'abandon d'un équipage : sa spéciale et son motif sont ceux du début de l'arrêt,
    même s'il est devenu définitif plus tard dans la journée."""
    rattachement = controles.get(arret[0].id_controle, _HORS_ITINERAIRE)
    return Abandon(
        equipage,
        None if rattachement.speciale is None else _code_speciale(rattachement.speciale),
        rattachement.controle,
        arret[0].motif,
        peut_repartir=rallye_en_cours and arret[-1].statut == _ABANDON_PROVISOIRE,
    )


def _lire_championnats(brut: Any) -> dict[str, int]:
    """Nom du championnat -> identifiant, pour une saison."""
    return {c["name"]: int(c["championshipId"]) for c in brut["championships"]}


@dataclass(frozen=True)
class _Participant:
    nom: str
    nationalite: str | None
    constructeur: str
    equipe: str | None


@dataclass(frozen=True)
class _DetailChampionnat:
    participants: dict[int, _Participant]
    # Identifiant de l'épreuve -> (numéro dans la saison, nom du rallye).
    rallyes: dict[int, tuple[int, str]]


@dataclass(frozen=True)
class _ResultatRallye:
    id_rallye: int
    statut: str
    position: str
    points: int
    termes: list[int] | None
    decompte: bool


@dataclass(frozen=True)
class _Resultat:
    id_participant: int
    position: int
    points: int
    rallyes: list[_ResultatRallye]


# Le statut d'un équipage sur un rallye ; « DidNotEnter » (non engagé) est omis.
_STATUTS = {
    "Finished": "classé",
    "RetiredAccident": "abandon",
    "RetiredMechanical": "abandon",
    "RetiredWithdrawn": "abandon",
    "DidNotStart": "non partant",
    "ForceMajeure": "force majeure",
}
_NON_ENGAGE = "DidNotEnter"

# L'ordre des termes du détail des points d'un pilote ou d'un copilote, vérifié sur
# la Power Stage du Rally Sweden 2026 : le troisième terme n'est publié que pour
# les cinq premiers de la Power Stage.
_TERMES = ("classement_final", "dimanche", "power_stage")


def _lire_detail_championnat(brut: Any) -> _DetailChampionnat:
    rallyes = {
        int(m["eventId"]): (int(m["order"]), m["event"]["name"])
        for m in brut["championshipRounds"]
    }
    return _DetailChampionnat(_lire_participants(brut), rallyes)


def _lire_participants(brut: Any) -> dict[int, _Participant]:
    """Le sens des cinq champs génériques de chaque participant est donné par les
    descriptions du championnat."""
    rangs = ("One", "Two", "Three", "Four", "Five")
    participants = {}
    for entree in brut["championshipEntries"]:
        champs = {
            brut[f"field{r}Description"]: entree[f"field{r}"]
            for r in rangs
            if entree[f"field{r}"] not in (None, "", "None")
        }
        # Un nom de famille peut manquer (un copilote WRC2 n'est publié que « MJ »).
        nom = " ".join(champs[c] for c in ("FirstName", "LastName") if c in champs) or champs["Name"]
        participants[int(entree["championshipEntryId"])] = _Participant(
            nom=nom,
            nationalite=champs.get("CountryISO3"),
            constructeur=champs["Manufacturer"],
            equipe=champs.get("ManufacturerFull") or champs.get("Entrant"),
        )
    return participants


def _lire_resultats(brut: Any) -> list[_Resultat]:
    return [
        _Resultat(
            id_participant=int(r["championshipEntryId"]),
            position=int(r["overallPosition"]),
            points=int(r["overallPoints"]),
            rallyes=[_lire_resultat_rallye(rr) for rr in r["roundResults"]],
        )
        for r in brut["entryResults"]
    ]


def _lire_resultat_rallye(brut: Any) -> _ResultatRallye:
    # Le détail vaut « R », « - »… sans points ; un équipage reparti en Super Rally
    # peut toutefois marquer le dimanche ou en Power Stage sans être classé.
    detail = brut["pointsBreakdown"]
    chiffre = re.fullmatch(r"\d+( \+ \d+)*", detail) is not None
    return _ResultatRallye(
        id_rallye=int(brut["eventId"]),
        statut=brut["status"],
        position=brut["position"],
        points=int(brut["totalPoints"]),
        termes=[int(t) for t in detail.split("+")] if chiffre else None,
        decompte=bool(brut["dropped"]),
    )


def _assembler(
    detail: _DetailChampionnat, resultats: list[_Resultat], detailler: bool
) -> list[LigneChampionnat]:
    lignes = []
    for resultat in sorted(resultats, key=lambda r: r.position):
        participant = detail.participants[resultat.id_participant]
        rallyes = [
            _points_rallye(r, *detail.rallyes[r.id_rallye], detailler)
            for r in resultat.rallyes
            if r.statut != _NON_ENGAGE
        ]
        lignes.append(
            LigneChampionnat(
                position=resultat.position,
                nom=participant.nom,
                nationalite=participant.nationalite,
                constructeur=participant.constructeur,
                equipe=participant.equipe,
                points=resultat.points,
                rallyes=sorted(rallyes, key=lambda r: r.numero),
            )
        )
    return lignes


def _points_rallye(
    resultat: _ResultatRallye, numero: int, nom: str, detailler: bool
) -> PointsRallye:
    termes = resultat.termes
    # La position d'un constructeur est publiée de façon incohérente (« 1 » ou
    # « 1 + 2 + 1 + 3 » pour un même détail) : elle n'est pas reprise.
    classe = resultat.statut == "Finished" and detailler
    return PointsRallye(
        numero=numero,
        rallye=nom,
        statut=_STATUTS.get(resultat.statut, resultat.statut),
        position_rallye=resultat.position if classe else None,
        points=resultat.points,
        detail=None if termes is None else " + ".join(map(str, termes)),
        points_detailles=dict(zip(_TERMES, termes)) if termes is not None and detailler else None,
        compte=not resultat.decompte,
    )
