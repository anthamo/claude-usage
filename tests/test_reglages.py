import tempfile
import unittest
from pathlib import Path

from claude_usage import reglages


class TestReglages(unittest.TestCase):
    def test_defaut(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(reglages.charger(Path(d) / "absent.json"), {"auto": False})

    def test_illisible_ou_mal_forme(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "r.json"
            for contenu in ("{pas du json", '{"auto": "oui"}', "[]"):
                chemin.write_text(contenu)
                self.assertEqual(reglages.charger(chemin), {"auto": False})

    def test_aller_retour(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "sous" / "r.json"
            reglages.enregistrer({"auto": True}, chemin)
            self.assertEqual(reglages.charger(chemin), {"auto": True})
            reglages.enregistrer({"auto": False}, chemin)
            self.assertEqual(reglages.charger(chemin), {"auto": False})


if __name__ == "__main__":
    unittest.main()
