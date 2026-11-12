"""Le relevé : sa forme, son stockage, la traduction des deux sources, l'état donné à la page."""

import json
import math
import os
import tempfile
from pathlib import Path

DOSSIER = Path("~/Library/Application Support/claude-usage").expanduser()
CHEMIN = DOSSIER / "releve.json"

ESPACE_INSECABLE = " "


def _nombre(valeur):
    # bool est un int en Python : True ne doit pas passer pour 1 %.
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
        return None
    if isinstance(valeur, float) and not math.isfinite(valeur):
        return None
    return valeur


def _borner(pourcentage):
    return max(0.0, min(100.0, float(pourcentage)))


def _fenetre(pourcentage, remise_a_zero):
    pourcentage = _nombre(pourcentage)
    remise_a_zero = _nombre(remise_a_zero)
    if pourcentage is None or remise_a_zero is None:
        return None
    return {"pourcentage": _borner(pourcentage), "remise_a_zero": int(remise_a_zero)}


def depuis_ligne(donnees, maintenant):
    """Traduit le JSON de la ligne d'état. None si aucune fenêtre n'est lisible."""
    if not isinstance(donnees, dict):
        return None
    limites = donnees.get("rate_limits")
    if not isinstance(limites, dict):
        return None

    def lire(cle):
        brut = limites.get(cle)
        if not isinstance(brut, dict):
            return None
        return _fenetre(brut.get("used_percentage"), brut.get("resets_at"))

    session, semaine = lire("five_hour"), lire("seven_day")
    if session is None and semaine is None:
        return None
    return {"session": session, "semaine": semaine,
            "releve_a": int(maintenant), "source": "ligne"}


def _fenetre_sonde(brut):
    if not isinstance(brut, dict):
        return None
    utilisation = _nombre(brut.get("utilization"))
    if utilisation is None:
        return None
    return _fenetre(utilisation * 100, brut.get("resetsAt"))


def depuis_sonde(lignes, maintenant):
    """Traduit la sortie stream-json de `claude -p` : le dernier rate_limit_event gagne."""
    dernier = None
    for ligne in lignes:
        try:
            objet = json.loads(ligne)
        except (ValueError, TypeError):
            continue
        if isinstance(objet, dict) and objet.get("type") == "rate_limit_event":
            dernier = objet
    if dernier is None:
        return None
    info = dernier.get("rate_limit_info")
    if not isinstance(info, dict):
        return None

    session = semaine = None
    fenetres = info.get("unifiedWindows")
    if isinstance(fenetres, dict):
        session = _fenetre_sonde(fenetres.get("five_hour"))
        semaine = _fenetre_sonde(fenetres.get("seven_day"))
    else:
        # Repli : une seule fenêtre au premier niveau, désignée par rateLimitType.
        fenetre = _fenetre_sonde(info)
        if info.get("rateLimitType") == "five_hour":
            session = fenetre
        elif info.get("rateLimitType") == "seven_day":
            semaine = fenetre
    if session is None and semaine is None:
        return None
    return {"session": session, "semaine": semaine,
            "releve_a": int(maintenant), "source": "sonde"}


def lire(chemin=None):
    chemin = Path(chemin) if chemin is not None else CHEMIN
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return donnees if isinstance(donnees, dict) else None


def ecrire_atomique(chemin, texte, mode=0o600):
    """Écrit d'un coup : un lecteur ne voit jamais un fichier à moitié écrit."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    descripteur, temporaire = tempfile.mkstemp(dir=chemin.parent, prefix=chemin.name + ".")
    try:
        with os.fdopen(descripteur, "w", encoding="utf-8") as fichier:
            fichier.write(texte)
        os.chmod(temporaire, mode)
        os.replace(temporaire, chemin)
    except BaseException:
        try:
            os.unlink(temporaire)
        except OSError:
            pass
        raise


def ecrire(releve, chemin=None):
    chemin = Path(chemin) if chemin is not None else CHEMIN
    ecrire_atomique(chemin, json.dumps(releve, ensure_ascii=False))


def fusionner(ancien, nouveau):
    """Le nouveau remplace l'ancien ; une fenêtre muette garde l'ancienne tant qu'elle n'est pas échue."""
    resultat = dict(nouveau)
    if not isinstance(ancien, dict):
        return resultat
    for cle in ("session", "semaine"):
        if resultat.get(cle) is not None:
            continue
        precedente = ancien.get(cle)
        if (isinstance(precedente, dict)
                and _nombre(precedente.get("remise_a_zero")) is not None
                and precedente["remise_a_zero"] > nouveau["releve_a"]):
            resultat[cle] = precedente
    return resultat


def _arrondi(pourcentage):
    return int(math.floor(pourcentage + 0.5))


def _fenetre_etat(fenetre, maintenant):
    if not isinstance(fenetre, dict):
        return None
    if fenetre["remise_a_zero"] <= maintenant:
        return {"pourcentage": 0, "remise_a_zero": fenetre["remise_a_zero"], "echue": True}
    return {"pourcentage": _arrondi(fenetre["pourcentage"]),
            "remise_a_zero": fenetre["remise_a_zero"], "echue": False}


def etat(releve, maintenant, actualisation=False, erreur=None, absent=False, reglages=None):
    """L'état décrit dans ARCHITECTURE.md, tel que la page le reçoit."""
    if absent:
        nom = "absent"
    elif erreur:
        nom = "erreur"
    elif releve:
        nom = "ok"
    else:
        nom = "vide"
    releve = releve or {}
    return {
        "etat": nom,
        "message": erreur if nom == "erreur" else None,
        "actualisation": bool(actualisation),
        "session": _fenetre_etat(releve.get("session"), maintenant),
        "semaine": _fenetre_etat(releve.get("semaine"), maintenant),
        "releve_a": releve.get("releve_a"),
        "reglages": reglages if reglages is not None else {"demarrage": False, "auto": False},
    }


def titre(etat):
    session = etat.get("session")
    if not session:
        return ""
    return f"{session['pourcentage']}{ESPACE_INSECABLE}%"


def niveau(pourcentage):
    if pourcentage is None or pourcentage < 75:
        return "normal"
    if pourcentage < 90:
        return "attention"
    return "limite"
