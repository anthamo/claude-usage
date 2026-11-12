"""L'actualisation à la demande : lance `claude -p` et lit le relevé dans sa sortie."""

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import releve


class SondeErreur(Exception):
    pass


class ClaudeAbsent(SondeErreur):
    pass


COMMANDE = ["-p", "ok", "--model", "haiku", "--output-format", "stream-json",
            "--verbose", "--max-turns", "1"]
DELAI = 60


def trouver_claude():
    # Une app lancée à l'ouverture de session n'a pas le PATH du terminal.
    trouve = shutil.which("claude")
    if trouve:
        return trouve
    for candidat in ("~/.local/bin/claude", "/opt/homebrew/bin/claude", "/usr/local/bin/claude"):
        chemin = Path(candidat).expanduser()
        if chemin.exists():
            return str(chemin)
    return None


def _lancer(commande, dossier):
    resultat = subprocess.run(commande, cwd=dossier, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=DELAI, check=True)
    return resultat.stdout


def relever(lancer=None, maintenant=None, claude=None):
    claude = claude or trouver_claude()
    if not claude:
        raise ClaudeAbsent("Claude Code n'est pas installé sur ce Mac.")
    lancer = lancer or _lancer
    maintenant = time.time() if maintenant is None else maintenant
    # Dossier vide : Claude Code n'y trouve ni projet ni CLAUDE.md à charger.
    with tempfile.TemporaryDirectory() as dossier:
        try:
            sortie = lancer([claude, *COMMANDE], dossier)
        except subprocess.TimeoutExpired:
            raise SondeErreur("Claude Code n'a pas répondu à temps.") from None
        except (subprocess.CalledProcessError, OSError):
            raise SondeErreur("Claude Code ne répond pas.") from None
    resultat = releve.depuis_sonde((sortie or "").splitlines(), maintenant)
    if resultat is None:
        raise SondeErreur("Claude Code ne répond pas comme prévu.")
    return resultat
