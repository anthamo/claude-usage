"""Les préférences de l'app."""

import json
from pathlib import Path

from . import releve

CHEMIN = releve.DOSSIER / "reglages.json"


def charger(chemin=None):
    chemin = Path(chemin) if chemin is not None else CHEMIN
    auto = False
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
        if isinstance(donnees, dict) and isinstance(donnees.get("auto"), bool):
            auto = donnees["auto"]
    except (OSError, ValueError):
        pass
    return {"auto": auto}


def enregistrer(reglages, chemin=None):
    chemin = Path(chemin) if chemin is not None else CHEMIN
    releve.ecrire_atomique(chemin, json.dumps({"auto": bool(reglages.get("auto"))}))
