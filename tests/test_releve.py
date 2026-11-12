import json
import tempfile
import unittest
from pathlib import Path

from claude_usage import releve

SONDE_REELLE = json.dumps({"type": "rate_limit_event", "rate_limit_info": {
    "status": "allowed", "resetsAt": 1794528000, "rateLimitType": "five_hour",
    "unifiedWindows": {
        "five_hour": {"utilization": 0.49, "resetsAt": 1794528000, "status": "allowed"},
        "seven_day": {"utilization": 0.2, "resetsAt": 1794931200, "status": "allowed"}}}})
LIGNE_REELLE = {"rate_limits": {"five_hour": {"used_percentage": 49, "resets_at": 1794528000},
                                "seven_day": {"used_percentage": 20, "resets_at": 1794931200}}}


class TestDepuisLigne(unittest.TestCase):
    def test_deux_fenetres(self):
        r = releve.depuis_ligne(LIGNE_REELLE, 1794520000.7)
        self.assertEqual(r, {"session": {"pourcentage": 49.0, "remise_a_zero": 1794528000},
                             "semaine": {"pourcentage": 20.0, "remise_a_zero": 1794931200},
                             "releve_a": 1794520000, "source": "ligne"})

    def test_une_fenetre_absente(self):
        r = releve.depuis_ligne({"rate_limits": {"seven_day": {"used_percentage": 5, "resets_at": 9}}}, 1)
        self.assertIsNone(r["session"])
        self.assertEqual(r["semaine"]["pourcentage"], 5.0)

    def test_fenetre_mal_formee(self):
        r = releve.depuis_ligne({"rate_limits": {"five_hour": {"used_percentage": "x", "resets_at": 9},
                                                 "seven_day": {"used_percentage": 5, "resets_at": 9}}}, 1)
        self.assertIsNone(r["session"])
        self.assertIsNotNone(r["semaine"])

    def test_rien(self):
        self.assertIsNone(releve.depuis_ligne({}, 1))
        self.assertIsNone(releve.depuis_ligne({"rate_limits": {}}, 1))
        self.assertIsNone(releve.depuis_ligne(None, 1))

    def test_bornes(self):
        r = releve.depuis_ligne({"rate_limits": {"five_hour": {"used_percentage": 140, "resets_at": 9},
                                                 "seven_day": {"used_percentage": -3, "resets_at": 9}}}, 1)
        self.assertEqual(r["session"]["pourcentage"], 100.0)
        self.assertEqual(r["semaine"]["pourcentage"], 0.0)


class TestDepuisSonde(unittest.TestCase):
    def test_exemple_reel(self):
        r = releve.depuis_sonde(["pas du json", SONDE_REELLE, ""], 1794520000)
        self.assertEqual(r["session"], {"pourcentage": 49.0, "remise_a_zero": 1794528000})
        self.assertEqual(r["semaine"], {"pourcentage": 20.0, "remise_a_zero": 1794931200})
        self.assertEqual(r["source"], "sonde")

    def test_coherent_avec_la_ligne(self):
        a = releve.depuis_ligne(LIGNE_REELLE, 5)
        b = releve.depuis_sonde([SONDE_REELLE], 5)
        self.assertEqual(a["session"]["remise_a_zero"], b["session"]["remise_a_zero"])
        self.assertEqual(round(a["semaine"]["pourcentage"]), round(b["semaine"]["pourcentage"]))

    def test_le_dernier_gagne(self):
        autre = json.dumps({"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
            "five_hour": {"utilization": 0.6, "resetsAt": 10}}}})
        r = releve.depuis_sonde([SONDE_REELLE, '{"type":"result"}', autre], 1)
        self.assertEqual(r["session"]["pourcentage"], 60.0)
        self.assertIsNone(r["semaine"])

    def test_premier_niveau(self):
        ligne = json.dumps({"type": "rate_limit_event", "rate_limit_info": {
            "rateLimitType": "seven_day", "utilization": 0.3, "resetsAt": 77}})
        r = releve.depuis_sonde([ligne], 1)
        self.assertIsNone(r["session"])
        self.assertEqual(r["semaine"], {"pourcentage": 30.0, "remise_a_zero": 77})

    def test_aucune_fenetre(self):
        self.assertIsNone(releve.depuis_sonde(['{"type":"result"}', "bruit"], 1))
        vide = json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed"}})
        self.assertIsNone(releve.depuis_sonde([vide], 1))

    def test_borne(self):
        ligne = json.dumps({"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
            "five_hour": {"utilization": 1.3, "resetsAt": 10}}}})
        self.assertEqual(releve.depuis_sonde([ligne], 1)["session"]["pourcentage"], 100.0)


class TestDisque(unittest.TestCase):
    def test_aller_retour_et_absent(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "sous" / "releve.json"
            self.assertIsNone(releve.lire(chemin))
            r = releve.depuis_ligne(LIGNE_REELLE, 5)
            releve.ecrire(r, chemin)
            self.assertEqual(releve.lire(chemin), r)
            self.assertEqual(chemin.stat().st_mode & 0o777, 0o600)
            self.assertEqual([p.name for p in chemin.parent.iterdir()], ["releve.json"])

    def test_illisible(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            chemin.write_text("{pas du json")
            self.assertIsNone(releve.lire(chemin))


class TestFusionner(unittest.TestCase):
    def fen(self, p, reset):
        return {"pourcentage": p, "remise_a_zero": reset}

    def test_sans_ancien(self):
        n = {"session": None, "semaine": self.fen(1, 9), "releve_a": 5, "source": "ligne"}
        self.assertEqual(releve.fusionner(None, n), n)

    def test_remplace(self):
        a = {"session": self.fen(10, 100), "semaine": self.fen(10, 100), "releve_a": 1, "source": "sonde"}
        n = {"session": self.fen(20, 200), "semaine": self.fen(30, 300), "releve_a": 5, "source": "ligne"}
        self.assertEqual(releve.fusionner(a, n), n)

    def test_garde_l_ancienne_non_echue(self):
        a = {"session": self.fen(10, 100), "semaine": self.fen(10, 100), "releve_a": 1, "source": "sonde"}
        n = {"session": None, "semaine": self.fen(30, 300), "releve_a": 5, "source": "ligne"}
        r = releve.fusionner(a, n)
        self.assertEqual(r["session"], self.fen(10, 100))
        self.assertEqual(r["releve_a"], 5)
        self.assertEqual(r["source"], "ligne")

    def test_abandonne_l_ancienne_echue(self):
        a = {"session": self.fen(10, 100), "semaine": None, "releve_a": 1, "source": "sonde"}
        n = {"session": None, "semaine": self.fen(30, 300), "releve_a": 100, "source": "ligne"}
        self.assertIsNone(releve.fusionner(a, n)["session"])


class TestEtat(unittest.TestCase):
    R = {"session": {"pourcentage": 48.5, "remise_a_zero": 200},
         "semaine": {"pourcentage": 20.4, "remise_a_zero": 100}, "releve_a": 50, "source": "ligne"}

    def test_ok_arrondi(self):
        e = releve.etat(self.R, 99)
        self.assertEqual(e["etat"], "ok")
        self.assertIsNone(e["message"])
        self.assertEqual(e["session"], {"pourcentage": 49, "remise_a_zero": 200, "echue": False})
        self.assertEqual(e["semaine"]["pourcentage"], 20)
        self.assertEqual(e["releve_a"], 50)
        self.assertEqual(e["reglages"], {"demarrage": False, "auto": False})
        self.assertFalse(e["actualisation"])

    def test_fenetre_echue(self):
        e = releve.etat(self.R, 100)
        self.assertEqual(e["semaine"], {"pourcentage": 0, "remise_a_zero": 100, "echue": True})
        self.assertFalse(e["session"]["echue"])

    def test_vide(self):
        e = releve.etat(None, 1)
        self.assertEqual((e["etat"], e["session"], e["semaine"], e["releve_a"]), ("vide", None, None, None))

    def test_erreur_garde_les_fenetres(self):
        e = releve.etat(self.R, 1, erreur="Claude Code ne répond pas.", actualisation=True)
        self.assertEqual(e["etat"], "erreur")
        self.assertEqual(e["message"], "Claude Code ne répond pas.")
        self.assertEqual(e["session"]["pourcentage"], 49)
        self.assertTrue(e["actualisation"])

    def test_absent_prime(self):
        self.assertEqual(releve.etat(self.R, 1, erreur="x", absent=True)["etat"], "absent")

    def test_reglages(self):
        r = {"demarrage": True, "auto": True}
        self.assertEqual(releve.etat(None, 1, reglages=r)["reglages"], r)

    def test_fenetre_inconnue(self):
        r = dict(self.R, semaine=None)
        self.assertIsNone(releve.etat(r, 1)["semaine"])


class TestTitreNiveau(unittest.TestCase):
    def test_titre(self):
        e = releve.etat(TestEtat.R, 1)
        self.assertEqual(releve.titre(e), "49 %")
        self.assertEqual(releve.titre(releve.etat(None, 1)), "")

    def test_niveau(self):
        self.assertEqual(releve.niveau(None), "normal")
        self.assertEqual(releve.niveau(74), "normal")
        self.assertEqual(releve.niveau(75), "attention")
        self.assertEqual(releve.niveau(89), "attention")
        self.assertEqual(releve.niveau(90), "limite")


if __name__ == "__main__":
    unittest.main()
