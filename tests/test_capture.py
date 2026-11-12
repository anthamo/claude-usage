import io
import json
import tempfile
import unittest
from pathlib import Path

from claude_usage import capture, releve

LIGNE = json.dumps({"rate_limits": {"five_hour": {"used_percentage": 49, "resets_at": 2000},
                                     "seven_day": {"used_percentage": 20, "resets_at": 3000}}})


def lancer(texte, chemin, ancienne="", maintenant=1000):
    sortie = io.StringIO()
    code = capture.principal(io.StringIO(texte), sortie, chemin, maintenant, ancienne)
    return code, sortie.getvalue()


class TestCapture(unittest.TestCase):
    def test_ecrit_et_affiche(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            code, sortie = lancer(LIGNE, chemin)
            self.assertEqual(code, 0)
            self.assertEqual(sortie, "Session 49 % · Semaine 20 %\n")
            r = releve.lire(chemin)
            self.assertEqual(r["session"]["pourcentage"], 49.0)
            self.assertEqual(r["source"], "ligne")
            self.assertEqual(r["releve_a"], 1000)

    def test_une_seule_fenetre(self):
        with tempfile.TemporaryDirectory() as d:
            _, sortie = lancer(json.dumps({"rate_limits": {"seven_day": {
                "used_percentage": 7, "resets_at": 3000}}}), Path(d) / "r.json")
            self.assertEqual(sortie, "Semaine 7 %\n")

    def test_sans_rate_limits_n_ecrase_rien(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            lancer(LIGNE, chemin)
            avant = chemin.read_text()
            code, sortie = lancer(json.dumps({"model": {}}), chemin, maintenant=1500)
            self.assertEqual(code, 0)
            self.assertEqual(chemin.read_text(), avant)
            self.assertEqual(sortie, "Session 49 % · Semaine 20 %\n")

    def test_sans_rate_limits_et_sans_relevé_rien_ne_sort(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            code, sortie = lancer("{}", chemin)
            self.assertEqual((code, sortie), (0, ""))
            self.assertFalse(chemin.exists())

    def test_fusionne_avec_le_disque(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            lancer(LIGNE, chemin)
            lancer(json.dumps({"rate_limits": {"seven_day": {
                "used_percentage": 25, "resets_at": 3000}}}), chemin, maintenant=1100)
            r = releve.lire(chemin)
            self.assertEqual(r["session"]["pourcentage"], 49.0)
            self.assertEqual(r["semaine"]["pourcentage"], 25.0)

    def test_ancienne_commande(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            code, sortie = lancer(LIGNE, chemin, ancienne="cat >/dev/null; echo ancienne")
            self.assertEqual((code, sortie), (0, "ancienne\n"))
            self.assertEqual(releve.lire(chemin)["session"]["pourcentage"], 49.0)

    def test_ancienne_commande_recoit_le_json(self):
        with tempfile.TemporaryDirectory() as d:
            _, sortie = lancer(LIGNE, Path(d) / "r.json", ancienne="cat")
            self.assertEqual(sortie, LIGNE)

    def test_pas_du_json(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "releve.json"
            code, sortie = lancer("ceci n'est pas du json", chemin, ancienne="echo x")
            self.assertEqual(code, 0)
            self.assertFalse(chemin.exists())

    def test_ancienne_commande_en_echec_ne_plante_pas(self):
        with tempfile.TemporaryDirectory() as d:
            code, _ = lancer(LIGNE, Path(d) / "r.json", ancienne="exit 3")
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
