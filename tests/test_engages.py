from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from fakes import FausseHorloge, FauxTransport, fixture, outils

PARIS = ZoneInfo("Europe/Paris")


def le(annee: int, mois: int, jour: int, heure: int = 12) -> datetime:
    return datetime(annee, mois, jour, heure, tzinfo=PARIS)


def engages(rallye: str, quand: datetime = le(2026, 6, 1)) -> dict[str, Any]:
    return outils(FauxTransport(), FausseHorloge(quand)).engages(rallye)


def equipage(resultat: dict[str, Any], pilote: str) -> dict[str, Any]:
    return next(e for e in resultat["equipages"] if e["pilote"] == pilote)


def test_les_engages_d_un_rallye_designe_par_son_pays_donnent_l_equipage_et_sa_voiture() -> None:
    resultat = engages("Portugal")

    assert resultat["rallye"]["nom"] == "Vodafone Rally de Portugal"
    assert resultat["rallye"]["saison"] == 2026
    assert equipage(resultat, "Elfyn EVANS") == {
        "numero": "33",
        "pilote": "Elfyn EVANS",
        "copilote": "Scott MARTIN",
        "voiture": "GR Yaris Rally1",
        "categorie": "WRC1",
        "constructeur": "Toyota",
        "equipe": "TOYOTA GAZOO RACING WRT",
    }
    assert resultat["fraicheur"]["heure_donnee"] == "2026-06-01T12:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_seuls_les_equipages_wrc1_et_wrc2_sont_engages_les_autres_categories_sont_filtrees() -> None:
    resultat = engages("Portugal")

    categories = [e["categorie"] for e in resultat["equipages"]]
    assert categories.count("WRC1") == 11
    assert categories.count("WRC2") == 42
    assert equipage(resultat, "Andreas MIKKELSEN")["categorie"] == "WRC2"
    assert equipage(resultat, "Andreas MIKKELSEN")["equipe"] == "TOKSPORT WRT"
    pilotes = {e["pilote"] for e in resultat["equipages"]}
    # Une Rally2 sans priorité FIA, une Rally3 en WRC3, une autre en Junior, une Rally4.
    assert pilotes.isdisjoint(
        {"Óscar RAL", "Matteo FONTANA", "Calle CARLBERG", "Helder MIRANDA"}
    )


@pytest.mark.parametrize(
    ("designation", "nom"),
    [
        ("Rallye Monte Carlo", "Rallye Monte Carlo"),
        ("le Monte-Carlo", "Rallye Monte Carlo"),
        ("Gap", "Rallye Monte Carlo"),
        ("Rally de Portugal", "Vodafone Rally de Portugal"),
        ("Matosinhos", "Vodafone Rally de Portugal"),
        ("PORTUGAL", "Vodafone Rally de Portugal"),
        ("la Sardaigne", "Rally Italia Sardegna"),
        ("l'Italie", "Rally Italia Sardegna"),
        ("Alghero", "Rally Italia Sardegna"),
        ("Suède", "Rally Sweden"),
        ("Umea", "Rally Sweden"),
        ("le Chili", "Rally Chile Bío Bío"),
        ("Bio Bio", "Rally Chile Bío Bío"),
        ("les Canaries", "Rally Islas Canarias"),
        ("l'Acropole", "EKO Acropolis Rally Greece"),
        ("Jyvaskyla", "Secto Rally Finland"),
    ],
)
def test_un_rallye_se_designe_par_son_nom_son_pays_ou_sa_ville_sans_accents_ni_casse(
    designation: str, nom: str
) -> None:
    resultat = engages(designation)

    assert resultat.get("rallye", {}).get("nom") == nom


@pytest.mark.parametrize(
    ("designation", "quand", "nom"),
    [
        # Pendant le Rally de Portugal (du jeudi 7 au dimanche 10 mai 2026).
        ("en cours", le(2026, 5, 8), "Vodafone Rally de Portugal"),
        ("le rallye actuel", le(2026, 5, 10), "Vodafone Rally de Portugal"),
        ("ce week-end", le(2026, 5, 8), "Vodafone Rally de Portugal"),
        ("le dernier", le(2026, 5, 8), "Rally Islas Canarias"),
        ("le prochain", le(2026, 5, 8), "FORUM8 Rally Japan"),
        # Le mardi d'avant : le week-end à venir.
        ("ce weekend", le(2026, 5, 5), "Vodafone Rally de Portugal"),
        ("le dernier rallye", le(2026, 5, 5), "Rally Islas Canarias"),
        ("le prochain rallye", le(2026, 5, 5), "Vodafone Rally de Portugal"),
        # Le lendemain de l'arrivée.
        ("le dernier", le(2026, 5, 11), "Vodafone Rally de Portugal"),
        # Juste après le basculement sur la saison 2027.
        ("le dernier", le(2026, 10, 29), "Rally Italia Sardegna"),
        ("le prochain", le(2026, 10, 29), "Rallye Monte-Carlo"),
    ],
)
def test_un_rallye_se_designe_par_un_repere_relatif_selon_la_date_du_jour(
    designation: str, quand: datetime, nom: str
) -> None:
    resultat = engages(designation, quand)

    assert resultat.get("rallye", {}).get("nom") == nom


def avec_deux_rallyes_en_italie(transport: FauxTransport) -> FauxTransport:
    """La saison 2026, avec le Croatia Rally remplacé par un second rallye en Italie."""
    detail = fixture("season-detail-47.json")
    croatie = next(m["event"] for m in detail["seasonRounds"] if m["order"] == 4)
    croatie.update(name="Rally Sanremo", location="Sanremo, Liguria")
    croatie["country"].update(name="Italy", iso2="IT", iso3="ITA")
    transport.remplacer("season-detail.json?seasonId=47", detail)
    return transport


def test_si_la_designation_est_ambigue_les_candidats_sont_proposes_sans_choisir() -> None:
    transport = avec_deux_rallyes_en_italie(FauxTransport())

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).engages("l'Italie")

    assert "equipages" not in resultat
    assert "rallye" not in resultat
    assert [c["nom"] for c in resultat["candidats"]] == ["Rally Sanremo", "Rally Italia Sardegna"]


def test_une_designation_precise_leve_l_ambiguite() -> None:
    transport = avec_deux_rallyes_en_italie(FauxTransport())

    resultat = outils(transport, FausseHorloge(le(2026, 6, 1))).engages("Italie, en Sardaigne")

    assert resultat["rallye"]["nom"] == "Rally Italia Sardegna"


def test_un_rallye_introuvable_renvoie_les_rallyes_de_la_saison_comme_candidats() -> None:
    resultat = engages("la Nouvelle-Zélande")

    assert "equipages" not in resultat
    assert resultat["rallye_non_resolu"] == "la Nouvelle-Zélande"
    assert len(resultat["candidats"]) == 13
    assert resultat["candidats"][0]["statut"] == "passé"


def test_sans_rallye_en_cours_le_repere_en_cours_est_introuvable() -> None:
    # Entre le Rally Japan (fini le 31 mai) et l'Acropole (le 25 juin).
    resultat = engages("le rallye en cours", le(2026, 6, 10))

    assert "rallye" not in resultat
    assert len(resultat["candidats"]) == 13


def test_un_texte_qui_ne_designe_aucun_rallye_n_en_choisit_aucun() -> None:
    resultat = engages("le rallye")

    assert "rallye" not in resultat
    assert len(resultat["candidats"]) == 13


def appels_aux_engages(transport: FauxTransport) -> int:
    return sum(url.endswith("entries.json") for url in transport.appels)


def test_pendant_24_heures_les_engages_sont_reutilises_sans_rappeler_la_source() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    engages = outils(transport, horloge).engages
    engages("Portugal")

    horloge.avancer(timedelta(hours=23))
    resultat = engages("Portugal")

    assert appels_aux_engages(transport) == 1
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-08T14:00+02:00"


def test_apres_24_heures_les_engages_sont_redemandes_a_la_source() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    engages = outils(transport, horloge).engages
    engages("Portugal")

    horloge.avancer(timedelta(hours=25))
    resultat = engages("Portugal")

    assert appels_aux_engages(transport) == 2
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-09T15:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_si_la_source_est_en_panne_les_derniers_engages_connus_sont_renvoyes_comme_perimes() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    engages = outils(transport, horloge).engages
    engages("Portugal")

    horloge.avancer(timedelta(hours=25))
    transport.en_panne = True
    resultat = engages("Portugal")

    assert len(resultat["equipages"]) == 53
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-08T14:00+02:00"
    assert resultat["donnee_perimee"] is True


def test_si_les_engages_changent_de_format_les_derniers_connus_sont_renvoyes_comme_perimes() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    engages = outils(transport, horloge).engages
    engages("Portugal")

    horloge.avancer(timedelta(hours=25))
    transport.remplacer("events/640/rallies/708/entries.json", [{"pilote": "Evans"}])
    resultat = engages("Portugal")

    assert len(resultat["equipages"]) == 53
    assert resultat["donnee_perimee"] is True


def test_sans_engages_connus_et_source_en_panne_l_outil_nomme_le_rallye_sans_donnee() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    engages = outils(transport, horloge).engages
    engages("Suède")  # le calendrier est connu, pas les engagés du Portugal

    transport.en_panne = True
    resultat = engages("Portugal")

    assert resultat["rallye"]["nom"] == "Vodafone Rally de Portugal"
    assert resultat["donnee_disponible"] is False
    assert "equipages" not in resultat


def test_avant_publication_la_liste_des_engages_est_vide() -> None:
    resultat = engages("le prochain", le(2026, 10, 29))

    assert resultat["rallye"]["nom"] == "Rallye Monte-Carlo"
    assert resultat["rallye"]["saison"] == 2027
    assert resultat["equipages"] == []


def test_si_l_epreuve_change_de_format_les_derniers_engages_connus_sont_renvoyes_comme_perimes() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    engages = outils(transport, horloge).engages
    engages("Portugal")

    horloge.avancer(timedelta(hours=25))
    transport.remplacer("events/640.json", {"rallies": [{"rallyId": 708, "isMain": False}]})
    resultat = engages("Portugal")

    assert len(resultat["equipages"]) == 53
    assert resultat["donnee_perimee"] is True


@pytest.mark.parametrize(
    ("designation", "saison", "nom"),
    [
        ("le Portugal 2026", 2026, "Vodafone Rally de Portugal"),
        ("Monte-Carlo 2026", 2026, "Rallye Monte Carlo"),
        ("Monte-Carlo", 2027, "Rallye Monte-Carlo"),
        ("le dernier Monte-Carlo", 2026, "Rallye Monte Carlo"),
        ("le Monte-Carlo de l'an dernier", 2026, "Rallye Monte Carlo"),
        ("le prochain Monte-Carlo", 2027, "Rallye Monte-Carlo"),
        ("l'Italie 2026", 2026, "Rally Italia Sardegna"),
    ],
)
def test_juste_apres_le_basculement_un_rallye_de_la_saison_terminee_reste_designable(
    designation: str, saison: int, nom: str
) -> None:
    resultat = engages(designation, le(2026, 10, 29))

    assert resultat.get("rallye", {}).get("nom") == nom
    assert resultat["rallye"]["saison"] == saison


def test_en_janvier_avant_le_premier_rallye_le_dernier_est_celui_de_la_saison_precedente() -> None:
    resultat = engages("le dernier rallye", le(2027, 1, 5))

    assert resultat.get("rallye", {}).get("nom") == "Rally Italia Sardegna"
