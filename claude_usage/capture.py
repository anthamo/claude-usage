"""La commande de ligne d'état : note le relevé, puis écrit une ligne courte.

Ne doit jamais faire planter la ligne d'état de Claude Code : toute erreur est avalée.
"""

import json
import subprocess
import sys
import time

from . import ligne_etat, releve


def _ligne_par_defaut(donnees_releve):
    morceaux = []
    for cle, nom in (("session", "Session"), ("semaine", "Semaine")):
        fenetre = (donnees_releve or {}).get(cle)
        if fenetre:
            morceaux.append(f"{nom} {int(releve._arrondi(fenetre['pourcentage']))} %")
    return " · ".join(morceaux)


def principal(entree=None, sortie=None, chemin=None, maintenant=None, ancienne=None):
    """`ancienne` : None = lire la mémoire de l'app ; "" = pas d'ancienne commande (tests)."""
    entree = entree if entree is not None else sys.stdin
    sortie = sortie if sortie is not None else sys.stdout
    try:
        brut = entree.read()
        maintenant = time.time() if maintenant is None else maintenant
        donnees = json.loads(brut)
        courant = releve.lire(chemin)
        nouveau = releve.depuis_ligne(donnees, maintenant)
        if nouveau is not None:
            courant = releve.fusionner(courant, nouveau)
            releve.ecrire(courant, chemin)
    except Exception:
        return 0
    try:
        commande = ancienne if ancienne is not None else ligne_etat.ancienne_commande()
        if commande:
            resultat = subprocess.run(commande, shell=True, input=brut, capture_output=True,
                                      text=True, timeout=5)
            sortie.write(resultat.stdout)
        else:
            ligne = _ligne_par_defaut(courant)
            if ligne:
                sortie.write(ligne + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(principal())
