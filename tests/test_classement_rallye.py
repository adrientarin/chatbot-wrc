from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from chatbot_wrc.outils import DEFINITIONS
from fakes import FausseHorloge, FauxTransport, fixture, outils

PARIS = ZoneInfo("Europe/Paris")


def le(annee: int, mois: int, jour: int, heure: int = 12, minute: int = 0) -> datetime:
    return datetime(annee, mois, jour, heure, minute, tzinfo=PARIS)


def classement(
    rallye: str = "Portugal",
    apres_speciale: str | None = None,
    categorie: str = "toutes",
    quand: datetime = le(2026, 6, 1),
) -> dict[str, Any]:
    return outils(FauxTransport(), FausseHorloge(quand)).classement_rallye(
        rallye, apres_speciale, categorie
    )


def ligne(resultat: dict[str, Any], pilote: str) -> dict[str, Any]:
    return next(l for l in resultat["classement"] if l["pilote"] == pilote)


def test_sans_speciale_precisee_le_classement_est_celui_de_l_arrivee() -> None:
    resultat = classement("Portugal")

    assert resultat["rallye"]["nom"] == "Vodafone Rally de Portugal"
    assert resultat["speciale"]["code"] == "ES23"
    assert resultat["categorie"] == "toutes"
    assert resultat["classement"][:2] == [
        {
            "position": 1,
            "numero": "11",
            "pilote": "Thierry NEUVILLE",
            "copilote": "Martijn WYDAEGHE",
            "categorie": "WRC1",
            "constructeur": "Hyundai",
            "temps": "3:53:01.7",
            "ecart_au_leader": "0.0",
            "ecart_au_precedent": "0.0",
            "penalite": None,
            "super_rally": False,
            "super_rally_depuis": None,
        },
        {
            "position": 2,
            "numero": "99",
            "pilote": "Oliver SOLBERG",
            "copilote": "Elliott EDMONDSON",
            "categorie": "WRC1",
            "constructeur": "Toyota",
            "temps": "3:53:18.0",
            "ecart_au_leader": "16.3",
            "ecart_au_precedent": "16.3",
            "penalite": None,
            "super_rally": False,
            "super_rally_depuis": None,
        },
    ]
    assert resultat["classement"][2]["ecart_au_leader"] == "29.1"
    assert resultat["classement"][2]["ecart_au_precedent"] == "12.8"
    assert resultat["fraicheur"] == {
        "heure_donnee": "2026-06-01T12:00+02:00",
        "apres_speciale": "ES23",
    }
    assert resultat["donnee_perimee"] is False


def test_le_classement_apres_une_speciale_donnee_est_celui_de_ce_moment() -> None:
    resultat = classement("Portugal", "ES7")

    assert resultat["speciale"]["code"] == "ES7"
    assert resultat["classement"][0]["pilote"] == "Adrien FOURMAUX"
    assert resultat["classement"][0]["temps"] == "1:04:46.0"
    # La fraîcheur dit où en est le rallye, pas le moment demandé.
    assert resultat["fraicheur"]["apres_speciale"] == "ES23"


@pytest.mark.parametrize(
    ("designation", "code"),
    [("ES7", "ES7"), ("spéciale 7", "ES7"), ("la dernière", "ES23"), ("Power Stage", "ES23")],
)
def test_le_moment_se_designe_comme_une_speciale(designation: str, code: str) -> None:
    assert classement("Portugal", designation)["speciale"]["code"] == code


def test_filtrer_par_categorie_donne_les_positions_et_les_ecarts_dans_cette_categorie() -> None:
    resultat = classement("Portugal", None, "WRC2")

    assert resultat["categorie"] == "WRC2"
    assert {l["categorie"] for l in resultat["classement"]} == {"WRC2"}
    assert [
        (l["position"], l["pilote"], l["temps"], l["ecart_au_leader"], l["ecart_au_precedent"])
        for l in resultat["classement"][:3]
    ] == [
        (1, "Teemu SUNINEN", "4:04:15.5", "0.0", "0.0"),
        (2, "Nikolay GRYAZIN", "4:04:40.4", "24.9", "24.9"),
        (3, "Roope KORHONEN", "4:05:01.1", "45.6", "20.7"),
    ]


def test_sans_filtre_seuls_les_equipages_wrc1_et_wrc2_sont_classes() -> None:
    resultat = classement("Portugal")

    assert len(resultat["classement"]) == 34
    assert {l["categorie"] for l in resultat["classement"]} == {"WRC1", "WRC2"}


def test_une_categorie_non_suivie_est_une_requete_invalide() -> None:
    assert "WRC3" in classement("Portugal", None, "WRC3")["erreur"]


def test_une_penalite_est_signalee_avec_sa_duree_et_comptee_dans_le_cumul() -> None:
    resultat = classement("Portugal")

    assert ligne(resultat, "Joshua MCERLEAN")["penalite"] == "50.0"
    assert ligne(resultat, "Joshua MCERLEAN")["temps"] == "4:13:09.6"
    assert ligne(resultat, "Thierry NEUVILLE")["penalite"] is None


def test_une_penalite_n_apparait_qu_a_partir_du_moment_ou_elle_est_infligee() -> None:
    assert ligne(classement("Portugal", "ES1"), "Joshua MCERLEAN")["penalite"] is None
    assert ligne(classement("Portugal", "ES7"), "Joshua MCERLEAN")["penalite"] == "50.0"


def test_un_equipage_reparti_en_super_rally_est_signale_avec_son_abandon() -> None:
    resultat = classement("Portugal")

    assert ligne(resultat, "Robert VIRVES")["super_rally"] is True
    assert ligne(resultat, "Robert VIRVES")["super_rally_depuis"] == "ES1"
    assert ligne(resultat, "Thierry NEUVILLE")["super_rally"] is False
    assert ligne(resultat, "Thierry NEUVILLE")["super_rally_depuis"] is None


def test_le_super_rally_n_est_signale_qu_une_fois_l_equipage_reparti() -> None:
    avant_son_abandon = classement("Portugal", "ES7")
    apres_son_retour = classement("Portugal")

    assert ligne(avant_son_abandon, "Joshua MCERLEAN")["super_rally"] is False
    assert ligne(apres_son_retour, "Joshua MCERLEAN")["super_rally"] is True


def test_un_equipage_a_l_arret_n_est_pas_classe_meme_si_la_source_lui_donne_un_cumul() -> None:
    # Virves s'arrête à l'ES1 et repart à l'ES4 : la source lui a depuis attribué un temps.
    resultat = classement("Portugal", "ES1")

    assert "Robert VIRVES" not in [l["pilote"] for l in resultat["classement"]]
    assert abandon(resultat, "Robert VIRVES")["speciale"] == "ES1"


def test_un_equipage_reparti_redevient_classe() -> None:
    assert ligne(classement("Portugal", "ES7"), "Robert VIRVES")["super_rally"] is True
    assert "Robert VIRVES" not in [a["pilote"] for a in classement("Portugal", "ES7")["abandons"]]


def abandon(resultat: dict[str, Any], pilote: str) -> dict[str, Any]:
    return next(a for a in resultat["abandons"] if a["pilote"] == pilote)


def test_les_abandons_sont_listes_a_part_avec_leur_speciale() -> None:
    resultat = classement("Portugal")

    assert abandon(resultat, "Jon ARMSTRONG") == {
        "numero": "95",
        "pilote": "Jon ARMSTRONG",
        "copilote": "Shane BYRNE",
        "categorie": "WRC1",
        "speciale": "ES15",
        "controle": "SF15",
        "motif": "MECHANICAL",
        "peut_repartir": False,
    }
    assert len(resultat["abandons"]) == 17
    assert "Jon ARMSTRONG" not in [l["pilote"] for l in resultat["classement"]]


def test_les_abandons_sont_ceux_du_moment_demande() -> None:
    # Ces trois équipages ne repartent qu'à l'ES11 ; Armstrong ne s'arrête qu'à l'ES15.
    assert [a["pilote"] for a in classement("Portugal", "ES7")["abandons"]] == [
        "Tristan CHARPENTIER",
        "Alejandro CACHÓN",
        "Adrien MOSCA",
    ]
    assert "Jon ARMSTRONG" in [a["pilote"] for a in classement("Portugal", "ES15")["abandons"]]
    assert len(classement("Portugal", "ES15")["abandons"]) == 12


def test_un_abandon_entre_deux_speciales_se_rattache_a_la_precedente() -> None:
    assert abandon(classement("Portugal", "ES15"), "Eugen CĂRĂGUI")["speciale"] == "ES10"


def test_un_abandon_definitif_apres_un_super_rally_compte_a_sa_derniere_speciale() -> None:
    resultat = classement("Portugal")

    assert abandon(resultat, "Tristan CHARPENTIER")["speciale"] == "ES22"
    assert abandon(resultat, "Tristan CHARPENTIER")["controle"] == "SS22"


def test_un_abandon_devenu_definitif_garde_la_speciale_et_le_motif_de_son_arret() -> None:
    resultat = classement("dernier", quand=le(2026, 10, 27))

    assert abandon(resultat, "Giuseppe DETTORI")["speciale"] == "ES7"
    assert abandon(resultat, "Giuseppe DETTORI")["controle"] == "SF7"
    assert abandon(resultat, "Giuseppe DETTORI")["motif"] == "MECHANICAL"
    assert abandon(resultat, "Benjamin KORHOLA")["speciale"] == "ES3"
    assert abandon(resultat, "Benjamin KORHOLA")["controle"] == "SF3"


def test_les_abandons_suivent_le_filtre_par_categorie() -> None:
    assert [a["pilote"] for a in classement("Portugal", None, "WRC1")["abandons"]] == [
        "Jon ARMSTRONG"
    ]


def test_le_vainqueur_et_les_abandons_du_dernier_rallye() -> None:
    resultat = classement("le dernier rallye", quand=le(2026, 10, 27))

    assert resultat["rallye"]["nom"] == "Rally Italia Sardegna"
    assert resultat["classement"][0]["pilote"] == "Oliver SOLBERG"
    assert len(resultat["abandons"]) == 9


PORTUGAL_SAMEDI = le(2026, 5, 9, 11)
ADRESSE_RESULTATS_ES7 = "stages/10982/results.json?rallyId=708"
ADRESSE_ABANDONS = "events/640/retirements.json"
# La dernière ligne des abandons lue à ce moment-là : celle d'Adrien Mosca, au TC7.
DERNIER_ABANDON_ES7 = 11984
TC8 = 46410
MOSCA = next(
    e["entryId"]
    for e in fixture("entries-640-708.json")
    if e["driver"]["fullName"] == "Adrien MOSCA"
)


def abandons_jusqu_a_l_es7() -> list[dict[str, Any]]:
    return [
        r for r in fixture("retirements-640.json") if r["retirementId"] <= DERNIER_ABANDON_ES7
    ]


def rallye_en_cours(transport: FauxTransport, derniere_disputee: int = 7) -> FauxTransport:
    """Le Portugal arrêté à une spéciale, juste après l'abandon d'Adrien Mosca. Le statut
    « ToRun » d'une spéciale à venir n'a jamais pu être observé."""
    speciales = fixture("stages-640.json")
    for speciale in speciales:
        if speciale["number"] > derniere_disputee:
            speciale["status"] = "ToRun"
    transport.remplacer("events/640/stages.json", speciales)
    transport.remplacer(ADRESSE_ABANDONS, abandons_jusqu_a_l_es7())
    return transport


def abandon_de_mosca_au_controle(transport: FauxTransport, controle: int) -> FauxTransport:
    transport.remplacer(
        ADRESSE_ABANDONS,
        [r | {"controlId": controle} for r in abandons_jusqu_a_l_es7() if r["entryId"] == MOSCA],
    )
    return transport


def test_pendant_un_rallye_le_classement_est_celui_de_la_derniere_speciale_disputee() -> None:
    transport = rallye_en_cours(FauxTransport())

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).classement_rallye(
        "en cours", None, "toutes"
    )

    assert resultat["speciale"]["code"] == "ES7"
    assert resultat["fraicheur"]["apres_speciale"] == "ES7"
    assert resultat["classement"][0]["pilote"] == "Adrien FOURMAUX"


def test_un_abandon_provisoire_d_un_rallye_en_cours_peut_encore_repartir() -> None:
    transport = rallye_en_cours(FauxTransport())

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).classement_rallye(
        "Portugal", None, "toutes"
    )

    assert abandon(resultat, "Adrien MOSCA")["peut_repartir"] is True
    assert abandon(resultat, "Adrien MOSCA")["controle"] == "TC7"
    assert abandon(resultat, "Adrien MOSCA")["speciale"] == "ES7"
    assert "Adrien MOSCA" not in [l["pilote"] for l in resultat["classement"]]


def test_un_abandon_sur_le_controle_de_la_prochaine_speciale_est_deja_liste() -> None:
    transport = abandon_de_mosca_au_controle(rallye_en_cours(FauxTransport()), TC8)

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).classement_rallye(
        "Portugal", None, "toutes"
    )

    assert abandon(resultat, "Adrien MOSCA")["speciale"] == "ES8"
    assert abandon(resultat, "Adrien MOSCA")["controle"] == "TC8"
    assert "Adrien MOSCA" not in [l["pilote"] for l in resultat["classement"]]


def test_un_abandon_posterieur_au_moment_demande_n_est_pas_liste() -> None:
    transport = abandon_de_mosca_au_controle(FauxTransport(), TC8)

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", "ES7", "toutes"
    )

    assert resultat["abandons"] == []
    assert ligne(resultat, "Adrien MOSCA")["super_rally"] is False


def test_un_abandon_provisoire_d_un_rallye_termine_ne_peut_plus_repartir() -> None:
    transport = FauxTransport()
    transport.remplacer(ADRESSE_ABANDONS, abandons_jusqu_a_l_es7())

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", "ES7", "toutes"
    )

    assert abandon(resultat, "Adrien MOSCA")["peut_repartir"] is False


def appels(transport: FauxTransport, fin: str) -> int:
    return sum(a.endswith(fin) for a in transport.appels)


def test_pendant_un_rallye_le_classement_ne_date_pas_de_plus_d_une_minute() -> None:
    transport = rallye_en_cours(FauxTransport())
    horloge = FausseHorloge(PORTUGAL_SAMEDI)
    chatbot = outils(transport, horloge)
    chatbot.classement_rallye("Portugal", None, "toutes")

    horloge.avancer(timedelta(seconds=30))
    chatbot.classement_rallye("Portugal", None, "toutes")
    assert appels(transport, ADRESSE_RESULTATS_ES7) == 1
    assert appels(transport, ADRESSE_ABANDONS) == 1

    horloge.avancer(timedelta(seconds=31))
    resultat = chatbot.classement_rallye("Portugal", None, "toutes")
    assert appels(transport, ADRESSE_RESULTATS_ES7) == 2
    assert appels(transport, ADRESSE_ABANDONS) == 2
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-09T11:01+02:00"


def test_le_classement_d_un_rallye_termine_n_est_redemande_qu_une_fois_par_jour() -> None:
    transport = FauxTransport()
    horloge = FausseHorloge(le(2026, 6, 1))
    chatbot = outils(transport, horloge)
    chatbot.classement_rallye("Portugal", "ES7", "toutes")

    horloge.avancer(timedelta(hours=23))
    chatbot.classement_rallye("Portugal", "ES7", "toutes")
    assert appels(transport, ADRESSE_RESULTATS_ES7) == 1

    horloge.avancer(timedelta(hours=2))
    chatbot.classement_rallye("Portugal", "ES7", "toutes")
    assert appels(transport, ADRESSE_RESULTATS_ES7) == 2


def test_un_classement_lu_pendant_le_rallye_est_redemande_une_fois_le_rallye_termine() -> None:
    transport = rallye_en_cours(FauxTransport())
    horloge = FausseHorloge(le(2026, 5, 10, 11))
    chatbot = outils(transport, horloge)
    assert chatbot.classement_rallye("Portugal", None, "WRC1")["abandons"] == []

    transport.remplacer(ADRESSE_ABANDONS, fixture("retirements-640.json"))
    transport.remplacer("events/640/stages.json", fixture("stages-640.json"))
    horloge.avancer(timedelta(hours=20))  # le lundi : moins de 24 heures, rallye terminé
    resultat = chatbot.classement_rallye("Portugal", None, "WRC1")

    assert [a["pilote"] for a in resultat["abandons"]] == ["Jon ARMSTRONG"]
    assert resultat["donnee_perimee"] is False


def test_une_speciale_pas_encore_disputee_est_signalee_sans_classement() -> None:
    transport = rallye_en_cours(FauxTransport())

    resultat = outils(transport, FausseHorloge(PORTUGAL_SAMEDI)).classement_rallye(
        "Portugal", "ES8", "toutes"
    )

    assert resultat["pas_encore_disputee"] is True
    assert "classement" not in resultat
    assert resultat["fraicheur"]["apres_speciale"] == "ES7"
    assert resultat["donnee_disponible"] is True


def test_une_speciale_non_disputee_d_un_rallye_termine_n_est_pas_a_venir() -> None:
    transport = FauxTransport()
    speciales = fixture("stages-640.json")
    next(s for s in speciales if s["number"] == 8)["status"] = "Cancelled"
    transport.remplacer("events/640/stages.json", speciales)

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", "ES8", "toutes"
    )

    assert resultat["non_disputee"] is True
    assert "classement" not in resultat


def test_avant_la_premiere_arrivee_aucune_speciale_n_est_disputee() -> None:
    transport = rallye_en_cours(FauxTransport(), derniere_disputee=0)

    resultat = outils(transport, FausseHorloge(le(2026, 5, 7, 10))).classement_rallye(
        "Portugal", None, "toutes"
    )

    assert resultat["aucune_speciale_disputee"] is True
    assert "classement" not in resultat


def test_une_speciale_inexistante_est_signalee_avec_les_speciales_du_rallye() -> None:
    resultat = classement("Portugal", "ES99")

    assert resultat["speciale_non_resolue"] == "ES99"
    assert len(resultat["candidats"]) == 23


def test_un_rallye_ambigu_ou_introuvable_renvoie_les_candidats() -> None:
    resultat = classement("Bretagne")

    assert resultat["rallye_non_resolu"] == "Bretagne"
    assert len(resultat["candidats"]) == 13


def test_un_abandon_avant_la_premiere_speciale_n_a_pas_de_speciale() -> None:
    transport = abandon_de_mosca_au_controle(FauxTransport(), 46364)  # TC0, le départ

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", "ES7", "toutes"
    )

    assert abandon(resultat, "Adrien MOSCA")["speciale"] is None
    assert abandon(resultat, "Adrien MOSCA")["controle"] == "TC0"


def test_un_abandon_sur_un_controle_inconnu_reste_liste() -> None:
    transport = abandon_de_mosca_au_controle(FauxTransport(), 1)

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", "ES7", "toutes"
    )

    assert abandon(resultat, "Adrien MOSCA")["speciale"] is None
    assert abandon(resultat, "Adrien MOSCA")["controle"] is None


def test_en_panne_le_classement_connu_est_rendu_et_marque_comme_perime() -> None:
    transport = rallye_en_cours(FauxTransport())
    horloge = FausseHorloge(PORTUGAL_SAMEDI)
    chatbot = outils(transport, horloge)
    chatbot.classement_rallye("Portugal", None, "toutes")

    transport.en_panne = True
    horloge.avancer(timedelta(minutes=5))
    resultat = chatbot.classement_rallye("Portugal", None, "toutes")

    assert resultat["classement"][0]["pilote"] == "Adrien FOURMAUX"
    assert resultat["donnee_perimee"] is True
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-09T11:00+02:00"


def test_en_panne_sans_donnee_connue_le_chatbot_n_invente_rien() -> None:
    transport = FauxTransport()
    transport.en_panne = True

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", None, "toutes"
    )

    assert resultat["donnee_disponible"] is False
    assert "classement" not in resultat


@pytest.mark.parametrize(
    "adresse",
    [ADRESSE_RESULTATS_ES7, ADRESSE_ABANDONS, "events/640/itineraries/1425.json"],
)
def test_le_classement_est_indisponible_si_la_source_a_change_de_format(adresse: str) -> None:
    transport = FauxTransport()
    transport.remplacer(adresse, {"inattendu": True})

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_rallye(
        "Portugal", "ES7", "toutes"
    )

    assert resultat["donnee_disponible"] is False
    assert resultat["rallye"]["pays"] == "Portugal"
    assert "classement" not in resultat


def test_l_outil_est_declare_a_l_agent_et_executable() -> None:
    chatbot = outils(FauxTransport(), FausseHorloge(le(2026, 6, 1)))

    schema: Any = next(d for d in DEFINITIONS if d["name"] == "classement_rallye")["input_schema"]
    sans_moment = chatbot.executer(
        "classement_rallye", {"rallye": "Portugal", "categorie": "WRC1"}
    )
    avec_moment = chatbot.executer(
        "classement_rallye", {"rallye": "Portugal", "apres_speciale": "ES7", "categorie": "WRC1"}
    )

    # Obligatoire pour Claude : facultatif dans le schéma, il l'omet même pour « après l'ES7 ».
    assert set(schema["required"]) == {"rallye", "apres_speciale", "categorie"}
    assert sans_moment["speciale"]["code"] == "ES23"
    assert avec_moment["speciale"]["code"] == "ES7"
