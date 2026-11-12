# PLAN : Claude Usage

Écrit le 12/11/2026. Même méthode que Hue Controller : chaque tâche dit ses fichiers, son contrat, sa vérification.

## Règles pour l'exécutant

1. Lire `ARCHITECTURE.md` (les formes et le contrat) et `DESIGN.md` avant de coder ; ne pas les modifier, ni `PRD.md`.
2. Ne faire que la tâche demandée. Aucune dépendance de plus.
3. **Ne jamais lire d'identifiant** : ni trousseau, ni `~/.claude/.credentials.json`, ni variable d'environnement de jeton.
4. **Ne jamais lancer `claude`** pendant le développement ni dans les tests : la sonde se teste avec une sortie enregistrée.
5. **Ne jamais toucher au vrai `~/.claude/settings.json`** : les tests travaillent dans un dossier temporaire.
6. Noms en français. Commentaires : le pourquoi.
7. Finir par `uv run python -m unittest` et rapporter la sortie. Ne rien committer.

## Tranche unique : le MVP

| # | Tâche | Fichiers | Vérification |
| --- | --- | --- | --- |
| 1 | **Le relevé.** Lire, écrire, traduire la ligne d'état et la sonde, fabriquer l'état de la page (fenêtres échues comprises). | `releve.py`, tests | les deux exemples de `essais/sonde.md` donnent le même relevé ; une fenêtre échue sort à 0 % |
| 2 | **La capture.** La commande de ligne d'état. | `capture.py`, tests | un JSON de Claude Code sur l'entrée : le relevé est écrit, une ligne sort ; sans `rate_limits` : rien n'est écrasé |
| 3 | **La sonde.** Lancer `claude -p`, lire la sortie. | `sonde.py`, tests | sur une sortie enregistrée : le relevé ; `claude` introuvable, délai dépassé, sortie sans relevé : une erreur nommée |
| 4 | **La ligne d'état dans les réglages de Claude Code.** Installer, retirer, garder l'existante. | `ligne_etat.py`, tests | dossier temporaire : installation sur un fichier vide, sur un fichier avec une autre ligne d'état, retrait qui rend l'ancienne |
| 5 | **Préférences et lancement.** | `reglages.py`, `demarrage.py`, tests | comme Hue Controller |
| 6 | **La page.** | `panneau/` | navigateur, faux état : les quatre états, clair et sombre |
| 7 | **L'app.** | `app.py`, `__main__.py` | `--essai` |
| 8 | **Installation et documents.** | `installer.sh`, `README.md`, `INSTALLER_AVEC_CLAUDE.md` | relecture |
| 9 | **Revue et essai réel.** | | le pourcentage de la barre de menus égale celui de la page d'usage |
