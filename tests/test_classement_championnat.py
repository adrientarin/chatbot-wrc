from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fakes import FausseHorloge, FauxTransport, outils

PARIS = ZoneInfo("Europe/Paris")


def le(annee: int, mois: int, jour: int, heure: int = 12) -> datetime:
    return datetime(annee, mois, jour, heure, tzinfo=PARIS)


def test_le_classement_des_pilotes_wrc1_donne_les_points_et_les_ecarts() -> None:
    resultat = classement("WRC1", "pilotes")

    assert resultat["saison"] == 2026
    premiers = resultat["classement"][:3]
    assert [(l["position"], l["nom"], l["points"]) for l in premiers] == [
        (1, "Elfyn EVANS", 243),
        (2, "Oliver SOLBERG", 238),
        (3, "Sami PAJARI", 237),
    ]
    assert premiers[0]["nationalite"] == "GBR"
    assert premiers[0]["constructeur"] == "Toyota"
    assert premiers[0]["equipe"] == "TOYOTA GAZOO RACING WRT"
    assert [(l["ecart_au_leader"], l["ecart_au_precedent"]) for l in premiers] == [
        (0, 0),
        (5, 5),
        (6, 1),
    ]


def classement(categorie: str, type: str, quand: datetime = le(2026, 6, 1)) -> dict[str, Any]:
    return outils(FauxTransport(), FausseHorloge(quand)).classement_championnat(categorie, type)


def ligne(resultat: dict[str, Any], nom: str) -> dict[str, Any]:
    return next(l for l in resultat["classement"] if l["nom"] == nom)


def rallye(ligne: dict[str, Any], nom: str) -> dict[str, Any]:
    return next(r for r in ligne["rallyes"] if r["rallye"] == nom)


def test_les_points_de_chaque_rallye_sont_detailles_final_dimanche_et_power_stage() -> None:
    resultat = classement("WRC1", "pilotes")

    suede = rallye(ligne(resultat, "Elfyn EVANS"), "Rally Sweden")
    assert suede["numero"] == 2
    assert suede["position_rallye"] == "1"
    assert suede["points"] == 34
    assert suede["detail"] == "25 + 5 + 4"
    assert suede["points_detailles"] == {"classement_final": 25, "dimanche": 5, "power_stage": 4}
    # Neuville, 7e, a gagné la Power Stage sans marquer le dimanche.
    neuville = rallye(ligne(resultat, "Thierry NEUVILLE"), "Rally Sweden")
    assert neuville["points_detailles"] == {"classement_final": 6, "dimanche": 0, "power_stage": 5}
    # Hors du top 5 de la Power Stage : pas de points bonus.
    pajari = rallye(ligne(resultat, "Sami PAJARI"), "Rally Sweden")
    assert pajari["points_detailles"] == {"classement_final": 15, "dimanche": 2}


def test_les_rallyes_sont_dans_l_ordre_de_la_saison_et_ceux_non_disputes_sont_omis() -> None:
    virves = ligne(classement("WRC2", "pilotes"), "Robert VIRVES")

    assert [r["rallye"] for r in virves["rallyes"]] == [
        "Safari Rally Kenya",
        "EKO Acropolis Rally Greece",
        "Rally Estonia",
        "Secto Rally Finland",
        "Ueno Rally Del Paraguay",
        "Rally Chile Bío Bío",
        "Rally Italia Sardegna",
    ]


def podium(resultat: dict[str, Any]) -> list[tuple[str, int]]:
    return [(l["nom"], l["points"]) for l in resultat["classement"][:3]]


def test_le_classement_des_copilotes_wrc1() -> None:
    resultat = classement("WRC1", "copilotes")

    assert podium(resultat) == [
        ("Scott MARTIN", 243),
        ("Elliott EDMONDSON", 238),
        ("Marko SALMINEN", 237),
    ]


def test_le_classement_des_constructeurs_wrc1_garde_le_detail_tel_que_publie() -> None:
    resultat = classement("WRC1", "constructeurs")

    assert len(resultat["classement"]) == 4
    toyota = resultat["classement"][0]
    assert (toyota["nom"], toyota["constructeur"], toyota["points"]) == (
        "TOYOTA GAZOO RACING WRT",
        "Toyota",
        662,
    )
    assert toyota["nationalite"] is None
    assert podium(resultat)[1] == ("HYUNDAI SHELL MOBIS WORLD RALLY TEAM", 440)
    assert rallye(toyota, "Rally Sweden")["position_rallye"] is None
    suede = rallye(toyota, "Rally Sweden")
    assert sum(int(t) for t in suede["detail"].split("+")) == suede["points"]
    assert suede["points_detailles"] is None


def test_le_classement_des_pilotes_wrc2_signale_les_resultats_decomptes() -> None:
    resultat = classement("WRC2", "pilotes")

    assert podium(resultat) == [
        ("Robert VIRVES", 117),
        ("Roope KORHONEN", 94),
        ("Yohan ROSSEL", 85),
    ]
    virves = ligne(resultat, "Robert VIRVES")
    sardaigne = rallye(virves, "Rally Italia Sardegna")
    assert (sardaigne["points"], sardaigne["compte"]) == (17, False)
    assert sardaigne["points_detailles"] == {"classement_final": 17}
    assert rallye(virves, "Rally Chile Bío Bío")["compte"] is True


def test_le_classement_des_copilotes_wrc2() -> None:
    resultat = classement("WRC2", "copilotes")

    assert podium(resultat) == [
        ("Jakko VIILO", 117),
        ("Anssi VIINIKKA", 94),
        ("Arnaud DUNAND", 85),
    ]


def test_le_championnat_des_constructeurs_wrc2_n_existe_pas_et_c_est_dit_clairement() -> None:
    transport = FauxTransport()

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_championnat(
        "WRC2", "constructeurs"
    )

    assert "classement" not in resultat
    assert "WRC1" in resultat["erreur"]
    assert transport.appels == []


def test_une_categorie_hors_wrc1_et_wrc2_est_refusee() -> None:
    resultat = classement("WRC3", "pilotes")

    assert "classement" not in resultat
    assert "erreur" in resultat


def test_la_categorie_et_le_type_sont_compris_sans_tenir_compte_de_la_casse() -> None:
    resultat = classement("wrc1", "Pilotes")

    assert podium(resultat)[0] == ("Elfyn EVANS", 243)


def test_la_fraicheur_dit_apres_quel_rallye_et_a_quelle_heure() -> None:
    resultat = classement("WRC1", "pilotes", le(2026, 6, 1, 14))

    assert resultat["apres_rallye"] == {"numero": 13, "rallye": "Rally Italia Sardegna"}
    assert resultat["fraicheur"]["heure_donnee"] == "2026-06-01T14:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_juste_apres_le_basculement_le_classement_de_la_saison_terminee_reste_connu() -> None:
    resultat = classement("WRC1", "pilotes", le(2026, 10, 27))

    assert resultat["saison"] == 2027
    assert resultat["classement"] == []
    assert resultat["apres_rallye"] is None
    terminee = resultat["saison_terminee"]
    assert terminee["saison"] == 2026
    assert podium(terminee)[0] == ("Elfyn EVANS", 243)


def test_un_championnat_pas_encore_cree_pour_la_nouvelle_saison_est_signale() -> None:
    resultat = classement("WRC2", "pilotes", le(2026, 10, 27))

    assert resultat["saison"] == 2027
    assert resultat["championnat_publie"] is False
    assert resultat["classement"] == []
    assert resultat["saison_terminee"]["championnat_publie"] is True
    assert podium(resultat["saison_terminee"])[0] == ("Robert VIRVES", 117)


RESULTATS_WRC1_PILOTES = "championship-overall-results.json?championshipId=333&seasonId=47"


def test_pendant_24_heures_le_classement_est_reutilise_sans_rappeler_la_source() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 6, 1, 14))
    outil = outils(transport, horloge).classement_championnat
    outil("WRC1", "pilotes")
    appels_initiaux = len(transport.appels)

    horloge.avancer(timedelta(hours=23))
    resultat = outil("WRC1", "pilotes")

    assert len(transport.appels) == appels_initiaux
    assert resultat["fraicheur"]["heure_donnee"] == "2026-06-01T14:00+02:00"


def test_apres_24_heures_le_classement_est_redemande_a_la_source() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 6, 1, 14))
    outil = outils(transport, horloge).classement_championnat
    outil("WRC1", "pilotes")
    appels_initiaux = len(transport.appels)

    horloge.avancer(timedelta(hours=25))
    resultat = outil("WRC1", "pilotes")

    assert len(transport.appels) > appels_initiaux
    assert resultat["fraicheur"]["heure_donnee"] == "2026-06-02T15:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_si_la_source_est_en_panne_le_dernier_classement_connu_est_renvoye_comme_perime() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 6, 1, 14))
    outil = outils(transport, horloge).classement_championnat
    outil("WRC1", "pilotes")

    horloge.avancer(timedelta(hours=25))
    transport.en_panne = True
    resultat = outil("WRC1", "pilotes")

    assert podium(resultat)[0] == ("Elfyn EVANS", 243)
    assert resultat["fraicheur"]["heure_donnee"] == "2026-06-01T14:00+02:00"
    assert resultat["donnee_perimee"] is True


def test_si_le_classement_change_de_format_le_dernier_connu_est_renvoye_comme_perime() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 6, 1, 14))
    outil = outils(transport, horloge).classement_championnat
    outil("WRC1", "pilotes")

    horloge.avancer(timedelta(hours=25))
    transport.remplacer(RESULTATS_WRC1_PILOTES, {"standings": []})
    resultat = outil("WRC1", "pilotes")

    assert podium(resultat)[0] == ("Elfyn EVANS", 243)
    assert resultat["donnee_perimee"] is True


def test_sans_donnee_connue_et_source_en_panne_l_outil_dit_qu_il_n_a_pas_le_classement() -> None:
    transport = FauxTransport()
    transport.en_panne = True

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).classement_championnat(
        "WRC1", "pilotes"
    )

    assert resultat["donnee_disponible"] is False
    assert "classement" not in resultat


def test_un_abandon_apparait_dans_les_points_du_rallye_sans_position_ni_detail() -> None:
    solberg = ligne(classement("WRC1", "pilotes"), "Oliver SOLBERG")

    canaries = rallye(solberg, "Rally Islas Canarias")
    assert canaries["statut"] == "abandon"
    assert canaries["points"] == 0
    assert canaries["position_rallye"] is None
    assert canaries["detail"] is None
    assert rallye(solberg, "Rally Sweden")["statut"] == "classé"


def test_l_agent_peut_appeler_l_outil_par_son_nom() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2026, 6, 1))).executer(
        "classement_championnat", {"categorie": "WRC1", "type": "constructeurs"}
    )

    assert podium(resultat)[0] == ("TOYOTA GAZOO RACING WRT", 662)
