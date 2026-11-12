"""La ligne d'état dans les réglages de Claude Code : installer, retirer, garder l'existante."""

import json
import os
import shlex
import shutil
from pathlib import Path

from . import releve

REGLAGES_CLAUDE = Path("~/.claude/settings.json").expanduser()
MEMOIRE = releve.DOSSIER / "ligne_etat.json"
MARQUE = "claude_usage.capture"


def commande(uv=None, dossier=None):
    uv = uv or shutil.which("uv")
    if not uv:
        raise RuntimeError("uv est introuvable.")
    dossier = dossier or Path(__file__).resolve().parent.parent
    # Claude Code relance cette commande à chaque réponse : on passe par le Python du projet, qui démarre en quelques
    # dizaines de millisecondes, et par `uv run` seulement s'il n'est pas encore là.
    return (f"cd {shlex.quote(str(dossier))} && if [ -x .venv/bin/python ]; then .venv/bin/python -m {MARQUE}; "
            f"else {shlex.quote(str(uv))} run --quiet python -m {MARQUE}; fi")


def _lire(reglages_claude):
    """{} si le fichier est absent ; RuntimeError s'il est illisible (on n'écrase jamais)."""
    try:
        texte = reglages_claude.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        raise RuntimeError("Le fichier de réglages de Claude Code est illisible.") from None
    try:
        donnees = json.loads(texte)
    except ValueError:
        raise RuntimeError("Le fichier de réglages de Claude Code est illisible.") from None
    if not isinstance(donnees, dict):
        raise RuntimeError("Le fichier de réglages de Claude Code est illisible.")
    return donnees


def _ecrire(reglages_claude, donnees):
    mode = 0o600
    try:
        mode = reglages_claude.stat().st_mode & 0o777
    except OSError:
        pass
    releve.ecrire_atomique(reglages_claude,
                           json.dumps(donnees, indent=2, ensure_ascii=False) + "\n", mode)


def _est_la_notre(ligne):
    return (isinstance(ligne, dict) and isinstance(ligne.get("command"), str)
            and MARQUE in ligne["command"])


def installee(reglages_claude=None):
    reglages_claude = Path(reglages_claude) if reglages_claude is not None else REGLAGES_CLAUDE
    try:
        return _est_la_notre(_lire(reglages_claude).get("statusLine"))
    except RuntimeError:
        return False


def installer(reglages_claude=None, memoire=None, uv=None, dossier=None):
    reglages_claude = Path(reglages_claude) if reglages_claude is not None else REGLAGES_CLAUDE
    memoire = Path(memoire) if memoire is not None else MEMOIRE
    nouvelle = commande(uv, dossier)
    donnees = _lire(reglages_claude)
    if _est_la_notre(donnees.get("statusLine")):
        donnees["statusLine"]["command"] = nouvelle
        _ecrire(reglages_claude, donnees)
        return
    if reglages_claude.exists():
        shutil.copy2(reglages_claude,
                     reglages_claude.with_name(reglages_claude.name + ".avant-claude-usage"))
    releve.ecrire_atomique(memoire, json.dumps({"ancienne": donnees.get("statusLine")},
                                               ensure_ascii=False))
    donnees["statusLine"] = {"type": "command", "command": nouvelle}
    _ecrire(reglages_claude, donnees)


def _lire_memoire(memoire):
    try:
        donnees = json.loads(memoire.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return donnees.get("ancienne") if isinstance(donnees, dict) else None


def retirer(reglages_claude=None, memoire=None):
    reglages_claude = Path(reglages_claude) if reglages_claude is not None else REGLAGES_CLAUDE
    memoire = Path(memoire) if memoire is not None else MEMOIRE
    donnees = _lire(reglages_claude)
    if not _est_la_notre(donnees.get("statusLine")):
        return
    ancienne = _lire_memoire(memoire)
    if ancienne is None:
        del donnees["statusLine"]
    else:
        donnees["statusLine"] = ancienne
    _ecrire(reglages_claude, donnees)
    try:
        os.unlink(memoire)
    except OSError:
        pass


def ancienne_commande(memoire=None):
    memoire = Path(memoire) if memoire is not None else MEMOIRE
    ancienne = _lire_memoire(memoire)
    if (isinstance(ancienne, dict) and ancienne.get("type") == "command"
            and isinstance(ancienne.get("command"), str)):
        return ancienne["command"]
    return None
