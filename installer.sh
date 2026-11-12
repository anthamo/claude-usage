#!/bin/sh
# Installe Claude Usage sur ce Mac. À relancer sans risque : chaque étape se refait à l'identique.
#
#   ./installer.sh
#
# Ce qu'il fait : prépare l'environnement Python, branche la ligne d'état de Claude Code (c'est elle qui donne la
# consommation), crée « Claude Usage » dans le dossier Applications, active le lancement à l'ouverture de session,
# puis ouvre l'app. Aucun identifiant n'est lu : l'app passe par Claude Code, déjà connecté sur ce Mac.
set -e
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "Il manque « uv », l'outil qui installe Python et ses bibliothèques."
    echo "L'installer (voir https://docs.astral.sh/uv/), puis relancer ./installer.sh"
    exit 1
fi
if ! command -v claude >/dev/null 2>&1; then
    echo "Il manque Claude Code : c'est lui qui donne la consommation de l'abonnement."
    echo "L'installer et s'y connecter (voir https://claude.com/claude-code), puis relancer ./installer.sh"
    exit 1
fi

echo "1/4  Préparation de l'environnement…"
uv sync --quiet

echo "2/4  Ligne d'état de Claude Code…"
uv run --quiet python -c "
from claude_usage import ligne_etat
deja = ligne_etat.installee()
ligne_etat.installer()
print('     Déjà en place.' if deja else '     Ajoutée à ~/.claude/settings.json (l\'ancien fichier est gardé à côté, en .avant-claude-usage).')
"

echo "3/4  Application et lancement à l'ouverture de session…"
APP="$(uv run --quiet python -c "from claude_usage import demarrage; print(demarrage.installer_app()); demarrage.activer()")"

echo "4/4  Ouverture de l'app…"
open "$APP"

echo "C'est prêt : la jauge est dans la barre de menus, en haut à droite."
echo "Le pourcentage apparaît dès que Claude Code a répondu une fois, ou tout de suite avec « Actualiser » dans le panneau."
echo "Pour la rouvrir : « Claude Usage » dans Spotlight ou le Launchpad."
