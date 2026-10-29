from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from fakes import FausseHorloge, FauxTransport, outils

PARIS = ZoneInfo("Europe/Paris")


def le(annee: int, mois: int, jour: int, heure: int = 12) -> datetime:
    return datetime(annee, mois, jour, heure, tzinfo=PARIS)


def fiche(nom: str, quand: datetime = le(2026, 10, 29)) -> dict[str, Any]:
    return outils(FauxTransport(), FausseHorloge(quand)).fiche_pilote(nom)


def test_la_fiche_d_un_pilote_wrc1_designe_par_son_nom() -> None:
    resultat = fiche("Ogier")

    assert resultat["pilote"] == {
        "nom": "Sébastien OGIER",
        "nationalite": "FRA",
        "categorie": "WRC1",
        "voiture": "GR Yaris Rally1",
        "constructeur": "Toyota",
        "equipe": "TOYOTA GAZOO RACING WRT",
        "copilote": "Vincent LANDAIS",
        "dernier_rallye": {"numero": 13, "rallye": "Rally Italia Sardegna"},
        "championnats": [
            {"categorie": "WRC1", "position": 4, "points": 189, "ecart_au_leader": 54},
        ],
    }
    assert resultat["saison"] == 2026
    assert resultat["fraicheur"]["heure_donnee"] == "2026-10-29T12:00+01:00"
    assert resultat["donnee_perimee"] is False


def test_la_fiche_d_un_pilote_wrc2_designe_sans_accents_donne_ses_deux_classements() -> None:
    resultat = fiche("leo rossel")

    pilote = resultat["pilote"]
    assert pilote["nom"] == "Léo ROSSEL"
    assert pilote["nationalite"] == "FRA"
    assert pilote["categorie"] == "WRC2"
    assert pilote["voiture"] == "Ypsilon HF"
    assert pilote["constructeur"] == "Lancia"
    assert pilote["equipe"] == "2C JUNIOR TEAM"
    assert pilote["copilote"] == "Guillaume MERCOIRET"
    # Le championnat du monde des pilotes classe aussi les pilotes WRC2 qui y marquent.
    assert pilote["championnats"] == [
        {"categorie": "WRC1", "position": 14, "points": 18, "ecart_au_leader": 225},
        {"categorie": "WRC2", "position": 7, "points": 64, "ecart_au_leader": 53},
    ]


def test_en_pleine_saison_la_fiche_porte_sur_la_saison_en_cours() -> None:
    resultat = fiche("Evans", quand=le(2026, 6, 1))

    assert resultat["saison"] == 2026
    assert resultat["pilote"]["copilote"] == "Scott MARTIN"
    assert resultat["pilote"]["championnats"][0]["position"] == 1


@pytest.mark.parametrize(
    ("designation", "nom"),
    [
        ("Thierry", "Thierry NEUVILLE"),
        ("NEUVILLE", "Thierry NEUVILLE"),
        ("Sébastien", "Sébastien OGIER"),
        ("Gregoire Munster", "Grégoire MUNSTER"),
        ("Jari-Matti", "Jari-Matti LATVALA"),
        ("Neuvile", "Thierry NEUVILLE"),
        ("Neuvlile", "Thierry NEUVILLE"),
        ("Katsuta Takamoto", "Takamoto KATSUTA"),
        ("Takamato", "Takamoto KATSUTA"),
        ("Seb", "Sébastien OGIER"),
        ("Taka", "Takamoto KATSUTA"),
        ("JML", "Jari-Matti LATVALA"),
        ("Olly", "Oliver SOLBERG"),
    ],
)
def test_un_pilote_se_designe_par_son_prenom_son_nom_ou_son_surnom_meme_avec_une_faute_de_frappe(
    designation: str, nom: str
) -> None:
    assert fiche(designation)["pilote"]["nom"] == nom


def test_une_designation_ambigue_renvoie_les_candidats_sans_choisir() -> None:
    resultat = fiche("Rossel")

    assert "pilote" not in resultat
    assert resultat["pilote_non_resolu"] == "Rossel"
    assert resultat["candidats"] == [
        {"nom": "Yohan ROSSEL", "categorie": "WRC2"},
        {"nom": "Léo ROSSEL", "categorie": "WRC2"},
    ]


def test_un_pilote_absent_de_la_saison_est_introuvable_et_les_noms_proches_sont_proposes() -> None:
    # Kalle Rovanperä ne court pas en 2026.
    resultat = fiche("Kalle Rovanperä")

    assert "pilote" not in resultat
    assert resultat["pilote_non_resolu"] == "Kalle Rovanperä"
    assert len(resultat["candidats"]) == 5
    assert resultat["donnee_disponible"] is True


def test_si_la_source_tombe_la_derniere_fiche_connue_est_rendue_marquee_perimee() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 10, 29))
    outil = outils(transport, horloge)
    outil.fiche_pilote("Ogier")
    transport.en_panne = True
    horloge.avancer(timedelta(hours=25))

    resultat = outil.fiche_pilote("Ogier")

    assert resultat["pilote"]["copilote"] == "Vincent LANDAIS"
    assert resultat["donnee_perimee"] is True
    assert resultat["fraicheur"]["heure_donnee"] == "2026-10-29T12:00+01:00"


def test_sans_aucune_donnee_la_fiche_est_indisponible() -> None:
    transport = FauxTransport()
    transport.en_panne = True

    resultat = outils(transport, FausseHorloge(le(2026, 10, 29))).fiche_pilote("Ogier")

    assert resultat["donnee_disponible"] is False


def test_sans_les_engages_la_fiche_reste_donnee_sans_voiture_ni_copilote() -> None:
    transport = FauxTransport()
    transport.remplacer("events/647/rallies/715/entries.json", "pas du JSON")

    resultat = outils(transport, FausseHorloge(le(2026, 10, 29))).fiche_pilote("Ogier")

    pilote = resultat["pilote"]
    assert (pilote["voiture"], pilote["copilote"]) == (None, None)
    assert (pilote["constructeur"], pilote["equipe"]) == ("Toyota", "TOYOTA GAZOO RACING WRT")
    assert pilote["championnats"][0]["position"] == 4
