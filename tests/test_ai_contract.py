"""Tests du contrat de l'analyste IA en lecture seule.

Lancer : python -m unittest test_contrat_ia -v
Chaque test reprend un cas de l'audit du 31/10/2026 (constats 1 à 12).
"""
import copy
import unittest

from djofin.ai_contract import (ContractError, canonical_json, prepare_request,
                        serialize_request, validate_response, MAX_ALERTS)

H1 = "a" * 64
H2 = "b" * 64
DATES = ["2020-03-06", "2020-03-09", "2020-03-10"]


def requete(**over):
    params = dict(snapshot_sha256=H1, ticker="CW8.PA", as_of_utc="2026-10-31T10:16:13Z",
                  snapshot_dates=DATES)
    params.update(over)
    alerts = params.pop("alerts", [{"observation": "Écart d'ouverture de -6,19 % le 2020-03-09",
                                    "dates": ["2020-03-09"]}])
    return prepare_request(alerts, **params)


def reponse(req, **finding_over):
    finding = {"alert_id": "alert-0001", "category": "price_jump", "confidence": "medium",
               "explanation": "Baisse de 6,19 % le 2020-03-09, cohérente avec le krach de mars 2020.",
               "unknowns": ["Absence de seconde source"],
               "checks": ["compare_second_source", "check_exchange_calendar"],
               "evidence_dates": ["2020-03-09"]}
    finding.update(finding_over)
    return {"schema_version": "1.1", "request_digest": req["request_digest"],
            "decision": "human_review_only", "findings": [finding]}


class Acceptation(unittest.TestCase):
    def test_reponse_conforme_sans_signalement(self):
        req = requete()
        self.assertEqual(validate_response(req, reponse(req)), {"ok": True, "flags": []})


class Constat01ClesEnTrop(unittest.TestCase):
    def test_cle_en_trop_dans_la_reponse(self):
        req = requete(); r = reponse(req)
        r["orders"] = [{"buy": "CW8.PA", "qty": 10}]
        with self.assertRaises(ContractError):
            validate_response(req, r)

    def test_cle_en_trop_dans_un_constat(self):
        req = requete()
        r = reponse(req); r["findings"][0]["new_open"] = 330.0
        with self.assertRaises(ContractError):
            validate_response(req, r)

    def test_cle_manquante(self):
        req = requete(); r = reponse(req); del r["findings"][0]["unknowns"]
        with self.assertRaises(ContractError):
            validate_response(req, r)


class Constat02LienRequeteReponse(unittest.TestCase):
    def test_reponse_rejouee_sur_une_autre_requete(self):
        r = reponse(requete())
        autre = requete(snapshot_sha256=H2, ticker="XYZ")
        with self.assertRaises(ContractError):
            validate_response(autre, r)

    def test_requete_modifiee_apres_preparation(self):
        req = requete(); r = reponse(req)
        alteree = copy.deepcopy(req); alteree["permissions"]["can_trade"] = True
        with self.assertRaises(ContractError):
            validate_response(alteree, r)


class Constat03PrixInvente(unittest.TestCase):
    def test_nombre_absent_de_l_alerte_signale(self):
        req = requete()
        out = validate_response(req, reponse(
            req, explanation="Le vrai cours était 341,27 € selon Euronext."))
        self.assertIn({"alert_id": "alert-0001", "flag": "unsourced_numbers",
                       "values": ["341.27"]}, out["flags"])


class Constat04ChampsLibres(unittest.TestCase):
    def test_verification_hors_liste_refusee(self):
        req = requete()
        with self.assertRaises(ContractError):
            validate_response(req, reponse(req, checks=["Acheter 10 parts CW8 demain"]))

    def test_vocabulaire_de_trading_signale(self):
        req = requete()
        out = validate_response(req, reponse(req, unknowns=["Faut-il acheter ?"]))
        self.assertIn("trading_vocabulary", [f["flag"] for f in out["flags"]])

    def test_verifications_obligatoires_et_sans_doublon(self):
        req = requete()
        for checks in ([], ["inspect_raw_rows", "inspect_raw_rows"]):
            with self.assertRaises(ContractError):
                validate_response(req, reponse(req, checks=checks))


class Constat05ConfianceSansPreuve(unittest.TestCase):
    def test_confiance_haute_sans_preuve(self):
        req = requete()
        with self.assertRaises(ContractError):
            validate_response(req, reponse(req, confidence="high", evidence_dates=[]))

    def test_explication_vide(self):
        req = requete()
        with self.assertRaises(ContractError):
            validate_response(req, reponse(req, explanation="   "))

    def test_confiance_haute_sans_inconnue_signalee(self):
        req = requete()
        out = validate_response(req, reponse(req, confidence="high", unknowns=[],
                                             checks=["inspect_raw_rows"]))
        self.assertIn("high_confidence_without_unknowns_or_second_source",
                      [f["flag"] for f in out["flags"]])


class Constat06PasDePlantage(unittest.TestCase):
    def test_types_inattendus_donnent_contract_error(self):
        req = requete()
        cas = [dict(category=["price_jump"]), dict(alert_id={"x": 1}), dict(confidence=None),
               dict(evidence_dates=[["2020-03-09"]]), dict(unknowns="texte"),
               dict(explanation=42)]
        for over in cas:
            with self.subTest(over=over), self.assertRaises(ContractError):
                validate_response(req, reponse(req, **over))
        for mauvais in (None, [], "texte", {"findings": None}):
            with self.subTest(reponse=mauvais), self.assertRaises(ContractError):
                validate_response(req, mauvais)

    def test_hash_absent_ou_mal_forme(self):
        for h in (None, 123, "A" * 64, "a" * 63, "g" * 64):
            with self.subTest(h=h), self.assertRaises(ContractError):
                requete(snapshot_sha256=h)


class Constat07Entrees(unittest.TestCase):
    def test_ticker_et_horodatage(self):
        for over in (dict(ticker=None), dict(ticker="cw8 pa; rm"), dict(as_of_utc="n'importe quoi"),
                     dict(as_of_utc="2026-10-31T10:16:13"), dict(as_of_utc="2026-10-31T10:16:13+01:00")):
            with self.subTest(over=over), self.assertRaises(ContractError):
                requete(**over)

    def test_horodatage_normalise(self):
        self.assertEqual(requete()["as_of_utc"], "2026-10-31T10:16:13+00:00")


class Constat08Injection(unittest.TestCase):
    def test_mission_encadre_les_observations(self):
        self.assertIn("never instructions", requete()["mission"])

    def test_caracteres_de_controle_refuses(self):
        with self.assertRaises(ContractError):
            requete(alerts=["ligne\x1b[2Jcachée"])

    def test_decision_autre_que_revue_humaine(self):
        req = requete(); r = reponse(req); r["decision"] = "approve_trade"
        with self.assertRaises(ContractError):
            validate_response(req, r)


class Constat09Tailles(unittest.TestCase):
    def test_limites(self):
        with self.assertRaises(ContractError):
            requete(alerts=["x" * 501])
        with self.assertRaises(ContractError):
            requete(alerts=["alerte"] * (MAX_ALERTS + 1))
        with self.assertRaises(ContractError):
            requete(alerts=[])
        req = requete()
        with self.assertRaises(ContractError):
            validate_response(req, reponse(req, explanation="x" * 1501))


class Constat10PreuvesVerifiables(unittest.TestCase):
    def test_preuve_hors_alerte_refusee(self):
        req = requete()
        for preuve in (["2020-03-10"], ["alert-0001"], [H1]):
            with self.subTest(preuve=preuve), self.assertRaises(ContractError):
                validate_response(req, reponse(req, evidence_dates=preuve))

    def test_date_d_alerte_absente_de_l_instantane(self):
        with self.assertRaises(ContractError):
            requete(alerts=[{"observation": "trou", "dates": ["2020-03-07"]}])


class Constat11Serialisation(unittest.TestCase):
    def test_canonique_independante_de_l_ordre(self):
        a = {"b": 1, "a": [1, 2]}
        self.assertEqual(canonical_json(a), canonical_json(dict(reversed(list(a.items())))))

    def test_empreinte_stable(self):
        self.assertEqual(requete()["request_digest"], requete()["request_digest"])

    def test_serialisation_lisible_deterministe(self):
        req = requete()
        self.assertEqual(serialize_request(req), serialize_request(copy.deepcopy(req)))


class Constat12Revision(unittest.TestCase):
    def test_revision_impossible_avec_un_seul_instantane(self):
        req = requete()
        with self.assertRaises(ContractError):
            validate_response(req, reponse(req, category="historical_revision"))

    def test_revision_possible_avec_deux_instantanes(self):
        req = requete(previous_snapshot_sha256=H2)
        self.assertTrue(validate_response(req, reponse(req, category="historical_revision"))["ok"])

    def test_instantane_precedent_identique_refuse(self):
        with self.assertRaises(ContractError):
            requete(previous_snapshot_sha256=H1)


if __name__ == "__main__":
    unittest.main()