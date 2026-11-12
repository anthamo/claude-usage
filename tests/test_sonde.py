import json
import subprocess
import unittest

from claude_usage import sonde

SORTIE = "\n".join([
    json.dumps({"type": "system", "subtype": "init"}),
    json.dumps({"type": "rate_limit_event", "rate_limit_info": {
        "status": "allowed", "resetsAt": 1794528000, "rateLimitType": "five_hour",
        "unifiedWindows": {
            "five_hour": {"utilization": 0.49, "resetsAt": 1794528000, "status": "allowed"},
            "seven_day": {"utilization": 0.2, "resetsAt": 1794931200, "status": "allowed"}}}}),
    json.dumps({"type": "result", "result": "ok"}),
])


class TestSonde(unittest.TestCase):
    def test_releve(self):
        appels = []

        def lancer(commande, dossier):
            appels.append((commande, dossier))
            return SORTIE

        r = sonde.relever(lancer=lancer, maintenant=1794520000, claude="/x/claude")
        self.assertEqual(r["session"]["pourcentage"], 49.0)
        self.assertEqual(r["semaine"]["pourcentage"], 20.0)
        self.assertEqual(r["source"], "sonde")
        self.assertEqual(appels[0][0], ["/x/claude", *sonde.COMMANDE])
        self.assertTrue(appels[0][1])

    def test_claude_absent(self):
        original = sonde.trouver_claude
        sonde.trouver_claude = lambda: None
        try:
            with self.assertRaises(sonde.ClaudeAbsent) as c:
                sonde.relever(lancer=lambda *a: SORTIE)
        finally:
            sonde.trouver_claude = original
        self.assertEqual(str(c.exception), "Claude Code n'est pas installé sur ce Mac.")
        self.assertIsInstance(c.exception, sonde.SondeErreur)

    def erreur(self, exception):
        def lancer(commande, dossier):
            raise exception
        with self.assertRaises(sonde.SondeErreur) as c:
            sonde.relever(lancer=lancer, claude="/x/claude")
        return str(c.exception)

    def test_delai(self):
        self.assertEqual(self.erreur(subprocess.TimeoutExpired("claude", 60)),
                         "Claude Code n'a pas répondu à temps.")

    def test_code_non_nul(self):
        self.assertEqual(self.erreur(subprocess.CalledProcessError(1, "claude")),
                         "Claude Code ne répond pas.")

    def test_oserror(self):
        self.assertEqual(self.erreur(OSError("boum")), "Claude Code ne répond pas.")

    def test_sortie_sans_releve(self):
        with self.assertRaises(sonde.SondeErreur) as c:
            sonde.relever(lancer=lambda *a: '{"type":"result"}\n', claude="/x/claude")
        self.assertEqual(str(c.exception), "Claude Code ne répond pas comme prévu.")

    def test_trouver_claude_rend_un_texte_ou_none(self):
        trouve = sonde.trouver_claude()
        self.assertTrue(trouve is None or isinstance(trouve, str))


if __name__ == "__main__":
    unittest.main()
