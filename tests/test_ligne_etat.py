import json
import tempfile
import unittest
from pathlib import Path

from claude_usage import ligne_etat


class TestLigneEtat(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        d = Path(self._d.name)
        self.reglages = d / "claude" / "settings.json"
        self.reglages.parent.mkdir()
        self.memoire = d / "app" / "ligne_etat.json"
        self.sauvegarde = self.reglages.with_name("settings.json.avant-claude-usage")

    def installer(self):
        ligne_etat.installer(self.reglages, self.memoire, uv="/bin/uv", dossier="/le projet")

    def lire(self):
        return json.loads(self.reglages.read_text(encoding="utf-8"))

    def test_commande(self):
        c = ligne_etat.commande(uv="/bin/uv", dossier="/le projet")
        self.assertEqual(c, "cd '/le projet' && if [ -x .venv/bin/python ]; then .venv/bin/python -m claude_usage.capture; "
                            "else /bin/uv run --quiet python -m claude_usage.capture; fi")

    def test_commande_sans_uv(self):
        import shutil
        original = shutil.which
        shutil.which = lambda nom: None
        try:
            with self.assertRaises(RuntimeError):
                ligne_etat.commande(dossier="/x")
        finally:
            shutil.which = original

    def test_fichier_absent(self):
        self.assertFalse(ligne_etat.installee(self.reglages))
        self.installer()
        self.assertTrue(ligne_etat.installee(self.reglages))
        self.assertEqual(self.lire()["statusLine"]["type"], "command")
        self.assertFalse(self.sauvegarde.exists())
        self.assertIsNone(ligne_etat.ancienne_commande(self.memoire))
        ligne_etat.retirer(self.reglages, self.memoire)
        self.assertEqual(self.lire(), {})
        self.assertFalse(self.memoire.exists())

    def test_autres_cles_conservees_dans_l_ordre(self):
        original = {"model": "opus", "permissions": {"allow": ["Bash(ls)"]}, "env": {"A": "é"}}
        self.reglages.write_text(json.dumps(original), encoding="utf-8")
        self.installer()
        donnees = self.lire()
        self.assertEqual(list(donnees), ["model", "permissions", "env", "statusLine"])
        for cle in original:
            self.assertEqual(donnees[cle], original[cle])
        self.assertEqual(json.loads(self.sauvegarde.read_text()), original)
        self.assertIn('"é"', self.reglages.read_text(encoding="utf-8"))
        ligne_etat.retirer(self.reglages, self.memoire)
        self.assertEqual(self.lire(), original)

    def test_autre_ligne_d_etat_memorisee_puis_rendue(self):
        ancienne = {"type": "command", "command": "~/ma-ligne.sh", "padding": 1}
        original = {"statusLine": ancienne, "model": "opus"}
        self.reglages.write_text(json.dumps(original), encoding="utf-8")
        self.installer()
        donnees = self.lire()
        self.assertEqual(list(donnees), ["statusLine", "model"])
        self.assertIn("claude_usage.capture", donnees["statusLine"]["command"])
        self.assertEqual(ligne_etat.ancienne_commande(self.memoire), "~/ma-ligne.sh")
        ligne_etat.retirer(self.reglages, self.memoire)
        self.assertEqual(self.lire(), original)
        self.assertFalse(self.memoire.exists())
        self.assertFalse(ligne_etat.installee(self.reglages))

    def test_ancienne_non_commande(self):
        self.reglages.write_text(json.dumps({"statusLine": {"type": "text", "text": "x"}}))
        self.installer()
        self.assertIsNone(ligne_etat.ancienne_commande(self.memoire))

    def test_deux_installations(self):
        original = {"statusLine": {"type": "command", "command": "ancienne"}}
        self.reglages.write_text(json.dumps(original), encoding="utf-8")
        self.installer()
        ligne_etat.installer(self.reglages, self.memoire, uv="/autre/uv", dossier="/ailleurs")
        self.assertIn("/autre/uv", self.lire()["statusLine"]["command"])
        self.assertEqual(json.loads(self.sauvegarde.read_text()), original)
        self.assertEqual(ligne_etat.ancienne_commande(self.memoire), "ancienne")
        ligne_etat.retirer(self.reglages, self.memoire)
        self.assertEqual(self.lire(), original)

    def test_json_illisible(self):
        self.reglages.write_text("{pas du json", encoding="utf-8")
        with self.assertRaises(RuntimeError) as c:
            self.installer()
        self.assertEqual(str(c.exception), "Le fichier de réglages de Claude Code est illisible.")
        self.assertEqual(self.reglages.read_text(encoding="utf-8"), "{pas du json")
        self.assertFalse(self.sauvegarde.exists())
        self.assertFalse(self.memoire.exists())

    def test_retirer_sans_installation_ne_fait_rien(self):
        original = {"statusLine": {"type": "command", "command": "ancienne"}}
        self.reglages.write_text(json.dumps(original), encoding="utf-8")
        ligne_etat.retirer(self.reglages, self.memoire)
        self.assertEqual(self.lire(), original)


if __name__ == "__main__":
    unittest.main()
