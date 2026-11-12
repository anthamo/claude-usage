#!/bin/sh
# Retire Claude Usage de ce Mac : la ligne d'état de Claude Code revient à ce qu'elle était, le lancement
# automatique et l'application sont supprimés. Le dossier du projet reste : le supprimer à la main.
cd "$(dirname "$0")"
pkill -f "python -m claude_usage$" 2>/dev/null
uv run --quiet python -c "
from claude_usage import ligne_etat, demarrage
ligne_etat.retirer()
demarrage.desactiver()
print(demarrage.emplacement_app())
" | while read -r app; do [ -d "$app" ] && rm -rf "$app" && echo "Supprimé : $app"; done
rm -rf "$HOME/Library/Application Support/claude-usage"
echo "Claude Usage est retiré. La ligne d'état de Claude Code est revenue à ce qu'elle était."
