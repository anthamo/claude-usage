# Installer Claude Usage avec Claude

Ouvrir [Claude Code](https://claude.com/claude-code) dans un terminal, sur le Mac où installer l'app, puis coller la consigne ci-dessous.

```text
Installe sur ce Mac l'application Claude Usage, qui affiche la consommation de mon abonnement Claude dans la barre de menus.
Dépôt : https://github.com/anthamo/claude-usage

Avance étape par étape et dis-moi ce que tu fais en une phrase à chaque fois. Parle-moi en français.

1. Vérifie le terrain : la version de macOS (`sw_vers -productVersion` ; l'app est faite pour macOS 26, préviens-moi
   si la version est plus ancienne), la présence de `git` et de `uv`, et que Claude Code est connecté à un abonnement
   (`claude auth status`). Si `uv` manque, explique-moi ce que c'est, donne-moi la commande d'installation officielle
   (https://docs.astral.sh/uv/) et attends mon accord avant de la lancer.
2. Demande-moi où ranger le projet (propose `~/Applications-code/claude-usage` ou un dossier de mon choix), puis clone
   le dépôt à cet endroit. Ne le mets pas dans un dossier synchronisé (iCloud, Dropbox).
3. Lis `README.md` et `installer.sh` avant de lancer quoi que ce soit. Dis-moi en trois lignes ce que le script va
   faire, et surtout ceci : il ajoute une ligne d'état à Claude Code en modifiant la clé `statusLine` de
   `~/.claude/settings.json` (l'ancien fichier est gardé à côté). Attends mon accord.
4. Lance les tests : `uv run python -m unittest`. S'ils échouent, arrête-toi et montre-moi l'erreur.
5. Lance `./installer.sh`.
6. Vérifie : `uv run python -m claude_usage --essai` doit répondre « panneau ouvert : True » ; « Claude Usage.app »
   doit exister dans /Applications (ou ~/Applications) ; dis-moi de regarder si la jauge est bien en haut à droite de
   l'écran, et de cliquer « Actualiser » dans le panneau pour voir mes deux pourcentages.
7. Termine par un résumé : où est le projet, où est l'application, comment l'ouvrir, comment la quitter, et comment
   tout retirer (`./desinstaller.sh`).

Règles à respecter :
- Ne lis jamais mes identifiants Claude : ni le trousseau, ni les fichiers de connexion de Claude Code. L'app n'en a
  pas besoin, toi non plus.
- Ne modifie `~/.claude/settings.json` que par `./installer.sh`, et seulement après mon accord de l'étape 3.
- N'utilise pas `sudo`. Si une étape demande plus de droits, explique-moi pourquoi et laisse-moi décider.
- Ne modifie pas le code du projet. Si quelque chose ne marche pas, montre-moi le message d'erreur exact et propose
  une cause, sans improviser un contournement.
```
