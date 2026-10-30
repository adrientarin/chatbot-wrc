from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from chatbot_wrc.outils import DEFINITIONS
from fakes import FausseHorloge, FauxTransport, fixture, outils

PARIS = ZoneInfo("Europe/Paris")


def le(annee: int, mois: int, jour: int, heure: int = 12, minute: int = 0) -> datetime:
    return datetime(annee, mois, jour, heure, minute, tzinfo=PARIS)


def temps(
    rallye: str = "Portugal",
    speciale: str = "ES7",
    categorie: str = "toutes",
    quand: datetime = le(2026, 6, 1),
) -> dict[str, Any]:
    return outils(FauxTransport(), FausseHorloge(quand)).temps_speciale(
        rallye, speciale, categorie
    )


def ligne(resultat: dict[str, Any], pilote: str) -> dict[str, Any]:
    return next(t for t in resultat["temps"] if t["pilote"] == pilote)


def test_les_temps_d_une_speciale_designee_par_son_numero_donnent_le_vainqueur_et_les_ecarts() -> None:
    resultat = temps("Portugal", "ES7")

    assert resultat["rallye"]["nom"] == "Vodafone Rally de Portugal"
    assert resultat["speciale"] == {
        "numero": 7,
        "code": "ES7",
        "nom": "Arganil 2",
        "distance_km": 18.62,
        "power_stage": False,
        "statut": "interrompue",
    }
    assert resultat["temps"][:2] == [
        {
            "position": 1,
            "numero": "1",
            "pilote": "Sébastien OGIER",
            "copilote": "Vincent LANDAIS",
            "categorie": "WRC1",
            "constructeur": "Toyota",
            "temps": "11:22.8",
            "ecart_au_meilleur": "0.0",
            "ecart_au_precedent": "0.0",
            "nature_du_temps": None,
        },
        {
            "position": 2,
            "numero": "11",
            "pilote": "Thierry NEUVILLE",
            "copilote": "Martijn WYDAEGHE",
            "categorie": "WRC1",
            "constructeur": "Hyundai",
            "temps": "11:25.4",
            "ecart_au_meilleur": "2.6",
            "ecart_au_precedent": "2.6",
            "nature_du_temps": None,
        },
    ]
    assert resultat["fraicheur"] == {
        "heure_donnee": "2026-06-01T12:00+02:00",
        "apres_speciale": "ES23",
    }
    assert resultat["donnee_perimee"] is False


def test_filtrer_par_categorie_donne_les_positions_et_les_ecarts_dans_cette_categorie() -> None:
    resultat = temps("Portugal", "Power Stage", "WRC2")

    assert resultat["categorie"] == "WRC2"
    assert {t["categorie"] for t in resultat["temps"]} == {"WRC2"}
    assert [
        (t["position"], t["pilote"], t["temps"], t["ecart_au_meilleur"], t["ecart_au_precedent"])
        for t in resultat["temps"][:3]
    ] == [
        (1, "Robert VIRVES", "7:13.245", "0.000", "0.000"),
        (2, "Yohan ROSSEL", "7:21.660", "8.415", "8.415"),
        (3, "Harry BATES", "7:24.274", "11.029", "2.614"),
    ]


def test_sans_filtre_seuls_les_equipages_wrc1_et_wrc2_sont_classes() -> None:
    resultat = temps("Portugal", "Power Stage")

    assert resultat["categorie"] == "toutes"
    assert len(resultat["temps"]) == 34
    assert {t["categorie"] for t in resultat["temps"]} == {"WRC1", "WRC2"}


def test_un_meme_temps_donne_une_meme_position_et_le_suivant_garde_son_rang() -> None:
    resultat = temps("Portugal", "ES7", "WRC1")
    forfait = temps("Portugal", "ES7", "WRC2")["temps"]

    assert [t["position"] for t in forfait[:4]] == [1, 1, 1, 1]
    assert forfait[1]["ecart_au_precedent"] == "0.0"
    assert [t["position"] for t in resultat["temps"][:5]] == [1, 2, 3, 4, 5]


def test_un_temps_qui_n_a_pas_ete_realise_sur_la_route_est_signale() -> None:
    assert ligne(temps("Portugal", "ES7"), "Roope KORHONEN")["nature_du_temps"] == "forfaitaire"
    assert ligne(temps("Portugal", "ES7"), "Elfyn EVANS")["nature_du_temps"] == "attribué"
    assert ligne(temps("Portugal", "ES1"), "Robert VIRVES")["nature_du_temps"] == "Super Rally"


def test_les_equipages_sans_temps_sont_listes_a_part() -> None:
    resultat = temps("Portugal", "Power Stage", "WRC2")

    assert resultat["sans_temps"] == [
        {"pilote": "Tristan CHARPENTIER", "categorie": "WRC2", "statut": "non partant"},
        {"pilote": "Ugur SOYLU", "categorie": "WRC2", "statut": "non partant"},
        {"pilote": "Ricardo FILIPE", "categorie": "WRC2", "statut": "non partant"},
        {"pilote": "Jorge MARTÍNEZ", "categorie": "WRC2", "statut": "non partant"},
    ]
    assert "Tristan CHARPENTIER" not in [t["pilote"] for t in resultat["temps"]]


def test_une_categorie_non_suivie_est_une_requete_invalide() -> None:
    assert "WRC3" in temps("Portugal", "ES7", "WRC3")["erreur"]


@pytest.mark.parametrize(
    ("designation", "numero"),
    [
        ("ES7", 7),
        ("es 7", 7),
        ("l'ES7", 7),
        ("spéciale 7", 7),
        ("la speciale 7", 7),
        ("SS7", 7),
        ("7", 7),
        ("la dernière", 23),
        ("la dernière spéciale", 23),
        ("derniere", 23),
        ("Power Stage", 23),
        ("la power stage", 23),
        ("powerstage", 23),
        ("PS", 23),
    ],
)
def test_une_speciale_se_designe_par_son_numero_ou_un_mot_cle(designation: str, numero: int) -> None:
    assert temps("Portugal", designation)["speciale"]["numero"] == numero


def test_la_power_stage_est_signalee_avec_les_temps_au_millieme() -> None:
    resultat = temps("Portugal", "Power Stage")

    assert resultat["speciale"]["power_stage"] is True
    assert resultat["temps"][0]["pilote"] == "Adrien FOURMAUX"
    assert resultat["temps"][0]["temps"] == "6:52.136"


@pytest.mark.parametrize("designation", ["ES99", "la spéciale de Fafe", ""])
def test_une_speciale_inexistante_est_signalee_avec_les_speciales_du_rallye(
    designation: str,
) -> None:
    resultat = temps("Portugal", designation)

    assert resultat["speciale_non_resolue"] == designation
    assert len(resultat["candidats"]) == 23
    assert resultat["candidats"][6]["code"] == "ES7"
    assert "temps" not in resultat


def test_un_rallye_ambigu_ou_introuvable_renvoie_les_candidats() -> None:
    resultat = temps("Bretagne", "ES7")

    assert resultat["rallye_non_resolu"] == "Bretagne"
    assert len(resultat["candidats"]) == 13


def test_les_speciales_non_publiees_ne_donnent_aucun_candidat() -> None:
    transport = FauxTransport()
    transport.remplacer("events/698/stages.json", [])

    resultat = outils(transport, FausseHorloge(le(2026, 10, 27))).temps_speciale(
        "prochain", "ES1", "toutes"
    )

    assert resultat["rallye"]["nom"] == "Rallye Monte-Carlo"
    assert resultat["speciale_non_resolue"] == "ES1"
    assert resultat["candidats"] == []


PORTUGAL_SAMEDI = le(2026, 5, 9, 11)
ADRESSE_ES7 = "stages/10982/stagetimes.json?rallyId=708"


def rallye_en_cours(transport: FauxTransport, derniere_disputee: int = 7) -> FauxTransport:
    """Le Portugal arrêté à une spéciale. Le statut d'une spéciale à venir n'a jamais pu
    être observé : « ToRun » en tient lieu, et la source peut en publier un autre."""
    speciales = fixture("stages-640.json")
    for speciale in speciales:
        if speciale["number"] > derniere_disputee:
            speciale["status"] = "ToRun"
    transport.remplacer("events/640/stages.json", speciales)
    # Les temps de l'ES1 tiennent lieu de ceux des spéciales sans fixture.
    temps_es1 = fixture("stagetimes-640-10976.json")
    transport.remplacer("stages/10981/stagetimes.json?rallyId=708", temps_es1)  # ES6
    transport.remplacer("stages/10997/stagetimes.json?rallyId=708", temps_es1)  # ES22
    transport.remplacer(
        "stages/10998/stagetimes.json?rallyId=708",
        fixture("stagetimes-640-10998.json") if derniere_disputee == 23 else [],
    )
    return transport


def test_pendant_un_rallye_la_derniere_speciale_est_la_derniere_disputee() -> None:
    transport = rallye_en_cours(FauxTransport())

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).temps_speciale(
        "en cours", "la dernière", "toutes"
    )

    assert resultat["speciale"]["code"] == "ES7"
    assert resultat["fraicheur"]["apres_speciale"] == "ES7"
    assert resultat["temps"][0]["pilote"] == "Sébastien OGIER"


@pytest.mark.parametrize("designation", ["ES8", "Power Stage"])
def test_une_speciale_pas_encore_disputee_est_signalee_sans_temps(designation: str) -> None:
    transport = rallye_en_cours(FauxTransport())

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).temps_speciale(
        "Portugal", designation, "toutes"
    )

    assert resultat["pas_encore_disputee"] is True
    assert resultat["temps"] == []
    assert resultat["speciale"]["statut"] == "ToRun"
    assert resultat["fraicheur"]["apres_speciale"] == "ES7"
    assert resultat["donnee_disponible"] is True


def test_une_speciale_en_train_de_se_courir_donne_les_temps_deja_publies() -> None:
    transport = rallye_en_cours(FauxTransport(), derniere_disputee=6)
    transport.remplacer(ADRESSE_ES7, fixture("stagetimes-640-10982.json")[:3])

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).temps_speciale(
        "Portugal", "ES7", "toutes"
    )

    assert "pas_encore_disputee" not in resultat
    assert [t["position"] for t in resultat["temps"]] == [1, 2, 3]
    assert resultat["fraicheur"]["apres_speciale"] == "ES6"


def test_pendant_un_rallye_les_temps_ne_datent_pas_de_plus_d_une_minute() -> None:
    transport = rallye_en_cours(FauxTransport())
    horloge = FausseHorloge(PORTUGAL_SAMEDI)
    chatbot = outils(transport, horloge)
    chatbot.temps_speciale("Portugal", "ES7", "toutes")

    horloge.avancer(timedelta(seconds=30))
    chatbot.temps_speciale("Portugal", "ES7", "toutes")
    assert sum(a.endswith(ADRESSE_ES7) for a in transport.appels) == 1

    horloge.avancer(timedelta(seconds=31))
    resultat = chatbot.temps_speciale("Portugal", "ES7", "toutes")
    assert sum(a.endswith(ADRESSE_ES7) for a in transport.appels) == 2
    # Le calendrier et les engagés, gardés 24 heures, ne vieillissent pas les temps.
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-09T11:01+02:00"


def test_pendant_un_rallye_une_nouvelle_speciale_apparait_en_moins_d_une_minute() -> None:
    transport = rallye_en_cours(FauxTransport(), derniere_disputee=6)
    horloge = FausseHorloge(PORTUGAL_SAMEDI)
    chatbot = outils(transport, horloge)
    avant = chatbot.temps_speciale("Portugal", "la dernière", "toutes")

    rallye_en_cours(transport, derniere_disputee=7)
    horloge.avancer(timedelta(seconds=61))
    apres = chatbot.temps_speciale("Portugal", "la dernière", "toutes")

    assert avant["fraicheur"]["apres_speciale"] == "ES6"
    assert apres["fraicheur"]["apres_speciale"] == "ES7"


def test_les_temps_d_un_rallye_termine_ne_sont_redemandes_qu_une_fois_par_jour() -> None:
    transport = FauxTransport()
    horloge = FausseHorloge(le(2026, 6, 1))
    chatbot = outils(transport, horloge)
    chatbot.temps_speciale("Portugal", "ES7", "toutes")

    horloge.avancer(timedelta(hours=23))
    chatbot.temps_speciale("Portugal", "ES7", "toutes")
    assert sum(a.endswith(ADRESSE_ES7) for a in transport.appels) == 1

    horloge.avancer(timedelta(hours=2))
    chatbot.temps_speciale("Portugal", "ES7", "toutes")
    assert sum(a.endswith(ADRESSE_ES7) for a in transport.appels) == 2


def test_une_donnee_lue_pendant_le_rallye_est_redemandee_une_fois_le_rallye_termine() -> None:
    transport = rallye_en_cours(FauxTransport(), derniere_disputee=22)
    horloge = FausseHorloge(le(2026, 5, 10, 11))
    chatbot = outils(transport, horloge)
    assert (
        chatbot.temps_speciale("Portugal", "la dernière", "toutes")["speciale"]["code"] == "ES22"
    )

    rallye_en_cours(transport, derniere_disputee=23)
    horloge.avancer(timedelta(hours=20))  # le lundi : moins de 24 heures, rallye terminé
    resultat = chatbot.temps_speciale("Portugal", "la dernière", "toutes")

    assert resultat["speciale"]["code"] == "ES23"
    assert resultat["donnee_perimee"] is False


def test_en_panne_les_temps_connus_sont_rendus_et_marques_comme_perimes() -> None:
    transport = FauxTransport()
    horloge = FausseHorloge(PORTUGAL_SAMEDI)
    chatbot = outils(transport, horloge)
    chatbot.temps_speciale("Portugal", "ES7", "toutes")

    transport.en_panne = True
    horloge.avancer(timedelta(minutes=5))
    resultat = chatbot.temps_speciale("Portugal", "ES7", "toutes")

    assert resultat["temps"][0]["pilote"] == "Sébastien OGIER"
    assert resultat["donnee_perimee"] is True
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-09T11:00+02:00"


def test_en_panne_sans_donnee_connue_le_chatbot_n_invente_rien() -> None:
    transport = FauxTransport()
    transport.en_panne = True

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).temps_speciale(
        "Portugal", "ES7", "toutes"
    )

    assert resultat["donnee_disponible"] is False
    assert "temps" not in resultat


def test_les_temps_sont_indisponibles_si_la_source_a_change_de_format() -> None:
    transport = FauxTransport()
    transport.remplacer(ADRESSE_ES7, {"inattendu": True})

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).temps_speciale(
        "Portugal", "ES7", "toutes"
    )

    assert resultat["donnee_disponible"] is False
    assert resultat["rallye"]["pays"] == "Portugal"


@pytest.mark.parametrize(
    "designation",
    ["Arganil 2", "Fafe 2", "avant-dernière", "la dernière spéciale de samedi"],
)
def test_une_designation_non_comprise_ne_choisit_pas_une_speciale_au_hasard(
    designation: str,
) -> None:
    resultat = temps("Portugal", designation)

    assert resultat["speciale_non_resolue"] == designation
    assert "temps" not in resultat


def test_la_power_stage_suivie_d_un_chiffre_reste_la_power_stage() -> None:
    assert temps("Portugal", "Power Stage 2")["speciale"]["numero"] == 23


def test_une_speciale_non_disputee_d_un_rallye_termine_n_est_pas_a_venir() -> None:
    transport = FauxTransport()
    speciales = fixture("stages-640.json")
    next(s for s in speciales if s["number"] == 8)["status"] = "Cancelled"
    transport.remplacer("events/640/stages.json", speciales)

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).temps_speciale(
        "Portugal", "ES8", "toutes"
    )

    assert "pas_encore_disputee" not in resultat
    assert resultat["non_disputee"] is True
    assert resultat["speciale"]["statut"] == "Cancelled"


def test_la_derniere_speciale_avant_la_premiere_arrivee_n_est_pas_une_speciale_inexistante() -> None:
    transport = rallye_en_cours(FauxTransport(), derniere_disputee=0)

    resultat = outils(transport, FausseHorloge(le(2026, 5, 7, 10))).temps_speciale(
        "Portugal", "la dernière", "toutes"
    )

    assert resultat["aucune_speciale_disputee"] is True
    assert "speciale_non_resolue" not in resultat
    assert "temps" not in resultat


def test_les_equipages_pas_encore_arrives_ne_sont_pas_listes_sans_temps() -> None:
    transport = rallye_en_cours(FauxTransport(), derniere_disputee=6)
    temps_es7 = fixture("stagetimes-640-10982.json")
    for t in temps_es7[3:]:
        t |= {"elapsedDurationMs": None, "position": None, "status": "Running"}
    transport.remplacer(ADRESSE_ES7, temps_es7)

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).temps_speciale(
        "Portugal", "ES7", "toutes"
    )

    assert len(resultat["temps"]) == 3
    assert resultat["sans_temps"] == []


def test_en_panne_une_speciale_non_disputee_n_est_pas_annoncee_comme_a_venir() -> None:
    transport = rallye_en_cours(FauxTransport())
    horloge = FausseHorloge(PORTUGAL_SAMEDI)
    chatbot = outils(transport, horloge)
    chatbot.temps_speciale("Portugal", "ES7", "toutes")

    transport.en_panne = True
    horloge.avancer(timedelta(minutes=5))
    resultat = chatbot.temps_speciale("Portugal", "ES8", "toutes")

    assert resultat["donnee_disponible"] is False
    assert "pas_encore_disputee" not in resultat


def test_une_precision_de_chronometrage_inconnue_ne_rend_pas_le_rallye_indisponible() -> None:
    transport = FauxTransport()
    speciales = fixture("stages-640.json")
    next(s for s in speciales if s["number"] == 23)["timingPrecision"] = None
    transport.remplacer("events/640/stages.json", speciales)

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).temps_speciale(
        "Portugal", "ES7", "toutes"
    )

    assert resultat["temps"][0]["temps"] == "11:22.8"


def test_le_vainqueur_de_la_power_stage_du_dernier_rallye() -> None:
    resultat = temps("le dernier rallye", "la Power Stage", quand=le(2026, 10, 27))

    assert resultat["rallye"]["nom"] == "Rally Italia Sardegna"
    assert resultat["speciale"]["statut"] == "interrompue"
    assert resultat["temps"][0]["pilote"] == "Thierry NEUVILLE"
    assert resultat["temps"][0]["temps"] == "4:54.201"


def test_l_outil_est_declare_a_l_agent_et_executable() -> None:
    chatbot = outils(FauxTransport(), FausseHorloge(le(2026, 6, 1)))

    schema: Any = next(d for d in DEFINITIONS if d["name"] == "temps_speciale")["input_schema"]
    resultat = chatbot.executer(
        "temps_speciale", {"rallye": "Portugal", "speciale": "ES7", "categorie": "WRC1"}
    )

    assert set(schema["required"]) == {"rallye", "speciale", "categorie"}
    assert resultat["categorie"] == "WRC1"
    assert len(resultat["temps"]) == 11
