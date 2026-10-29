from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fakes import FausseHorloge, FauxTransport, fixture, outils

PARIS = ZoneInfo("Europe/Paris")


def le(annee: int, mois: int, jour: int, heure: int = 12) -> datetime:
    return datetime(annee, mois, jour, heure, tzinfo=PARIS)


def test_le_statut_de_chaque_rallye_depend_de_la_date_du_jour() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2026, 5, 8))).calendrier()

    statuts = {r["nom"]: r["statut"] for r in resultat["rallyes"]}
    assert resultat["saison"] == 2026
    assert len(resultat["rallyes"]) == 13
    assert statuts["Rally Islas Canarias"] == "passé"
    assert statuts["Vodafone Rally de Portugal"] == "en cours"
    assert statuts["FORUM8 Rally Japan"] == "à venir"


def test_la_fraicheur_est_l_heure_a_laquelle_la_donnee_a_ete_recuperee() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))).calendrier()

    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-08T14:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_pendant_24_heures_le_calendrier_est_reutilise_sans_rappeler_la_source() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    calendrier = outils(transport, horloge).calendrier
    calendrier()
    appels_initiaux = len(transport.appels)

    horloge.avancer(timedelta(hours=23))
    resultat = calendrier()

    assert len(transport.appels) == appels_initiaux
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-08T14:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_apres_24_heures_le_calendrier_est_redemande_a_la_source() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    calendrier = outils(transport, horloge).calendrier
    calendrier()
    appels_initiaux = len(transport.appels)

    horloge.avancer(timedelta(hours=25))
    resultat = calendrier()

    assert len(transport.appels) > appels_initiaux
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-09T15:00+02:00"
    assert resultat["donnee_perimee"] is False


def test_si_la_source_est_en_panne_le_dernier_calendrier_connu_est_renvoye_comme_perime() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    calendrier = outils(transport, horloge).calendrier
    calendrier()

    horloge.avancer(timedelta(hours=25))
    transport.en_panne = True
    resultat = calendrier()

    assert len(resultat["rallyes"]) == 13
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-08T14:00+02:00"
    assert resultat["donnee_perimee"] is True


def test_si_la_source_change_de_format_le_dernier_calendrier_connu_est_renvoye_comme_perime() -> None:
    transport, horloge = FauxTransport(), FausseHorloge(le(2026, 5, 8, 14))
    calendrier = outils(transport, horloge).calendrier
    calendrier()

    horloge.avancer(timedelta(hours=25))
    transport.remplacer("season-detail.json?seasonId=47", {"rounds": []})
    resultat = calendrier()

    assert len(resultat["rallyes"]) == 13
    assert resultat["donnee_perimee"] is True


def test_sans_donnee_connue_et_source_en_panne_l_outil_dit_qu_il_n_a_pas_la_donnee() -> None:
    transport = FauxTransport()
    transport.en_panne = True

    resultat = outils(transport, FausseHorloge(le(2026, 5, 8, 14))).calendrier()

    assert resultat["donnee_disponible"] is False
    assert "rallyes" not in resultat


def saison_2027_non_publiee(transport: FauxTransport) -> FauxTransport:
    detail = fixture("season-detail-50.json")
    detail["seasonRounds"] = []
    transport.remplacer("season-detail.json?seasonId=50", detail)
    return transport


def test_une_fois_la_saison_terminee_et_la_suivante_publiee_la_saison_en_cours_bascule() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2026, 10, 27))).calendrier()

    assert resultat["saison"] == 2027
    assert resultat["rallyes"][0]["nom"] == "Rallye Monte-Carlo"
    assert resultat["rallyes"][0]["statut"] == "à venir"


def test_juste_apres_le_basculement_le_dernier_rallye_de_la_saison_terminee_reste_connu() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2026, 10, 27))).calendrier()

    terminee = resultat["saison_terminee"]
    assert terminee["saison"] == 2026
    assert terminee["rallyes"][-1]["nom"] == "Rally Italia Sardegna"
    assert terminee["rallyes"][-1]["statut"] == "passé"


def test_tant_que_la_saison_suivante_n_est_pas_publiee_la_saison_terminee_reste_en_cours() -> None:
    transport = saison_2027_non_publiee(FauxTransport())

    resultat = outils(transport, FausseHorloge(le(2026, 10, 27))).calendrier()

    assert resultat["saison"] == 2026
    assert all(r["statut"] == "passé" for r in resultat["rallyes"])


def test_le_calendrier_suivant_publie_en_cours_de_saison_ne_fait_pas_basculer() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2026, 6, 1))).calendrier()

    assert resultat["saison"] == 2026


def test_en_janvier_la_saison_precedente_reste_en_cours_tant_que_la_nouvelle_n_est_pas_publiee() -> None:
    transport = saison_2027_non_publiee(FauxTransport())

    resultat = outils(transport, FausseHorloge(le(2027, 1, 5))).calendrier()

    assert resultat["saison"] == 2026


def test_en_janvier_la_nouvelle_saison_publiee_est_en_cours() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2027, 1, 5))).calendrier()

    assert resultat["saison"] == 2027


def test_le_dernier_calendrier_connu_survit_au_redemarrage_de_l_application(tmp_path: Path) -> None:
    horloge = FausseHorloge(le(2026, 5, 8, 14))
    outils(FauxTransport(), horloge, dossier_cache=tmp_path).calendrier()

    horloge.avancer(timedelta(days=3))
    en_panne = FauxTransport()
    en_panne.en_panne = True
    resultat = outils(en_panne, horloge, dossier_cache=tmp_path).calendrier()

    assert len(resultat["rallyes"]) == 13
    assert resultat["fraicheur"]["heure_donnee"] == "2026-05-08T14:00+02:00"
    assert resultat["donnee_perimee"] is True


def test_en_janvier_avant_le_premier_rallye_la_saison_precedente_reste_connue() -> None:
    resultat = outils(FauxTransport(), FausseHorloge(le(2027, 1, 5))).calendrier()

    assert resultat["saison"] == 2027
    assert resultat["saison_terminee"]["saison"] == 2026
