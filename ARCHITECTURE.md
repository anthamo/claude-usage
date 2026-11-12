# ARCHITECTURE : Claude Usage

Écrit le 12/11/2026. Même socle que Hue Controller (`../hue-controller/ARCHITECTURE.md`) : une app Python (PyObjC) qui tient l'icône et la fenêtre en verre, une page HTML pour l'intérieur du panneau, des modules sans AppKit pour tout le reste.

## Vue d'ensemble

```
  Claude Code (terminal) --ligne d'état--> capture.py --écrit--> releve.json <--lit-- app.py --> la page
                                                                     ^
  bouton « Actualiser » --> sonde.py --> `claude -p "ok"` -----------+
```

## Les fichiers

| Fichier | Rôle | Dépend de |
| --- | --- | --- |
| `claude_usage/releve.py` | Le relevé : sa forme, sa lecture et son écriture sur disque, la traduction des deux sources vers cette forme, l'état donné à la page. Fonctions pures. | bibliothèque standard |
| `claude_usage/capture.py` | La commande de ligne d'état : lit le JSON de Claude Code, note le relevé, écrit une ligne courte. | `releve.py` |
| `claude_usage/sonde.py` | L'actualisation à la demande : lance `claude -p`, lit le relevé dans sa sortie. | `releve.py` |
| `claude_usage/ligne_etat.py` | Installe et retire la ligne d'état dans `~/.claude/settings.json`, avec sauvegarde. | bibliothèque standard |
| `claude_usage/reglages.py` | Les deux préférences de l'app. | bibliothèque standard |
| `claude_usage/demarrage.py` | Lancement à l'ouverture de session, lanceur dans le dossier Applications. | bibliothèque standard |
| `claude_usage/app.py` | L'icône, la fenêtre, la page. Seul fichier qui importe AppKit. | tout le reste, PyObjC |
| `claude_usage/panneau/` | La page : `index.html`, `panneau.css`, `panneau.js`, `faux.js`. | rien |

## Le relevé (`~/Library/Application Support/claude-usage/releve.json`)

```json
{"session": {"pourcentage": 49.0, "remise_a_zero": 1794528000},
 "semaine": {"pourcentage": 20.0, "remise_a_zero": 1794931200},
 "releve_a": 1794520000, "source": "ligne"}
```

`pourcentage` de 0 à 100 ; heures en secondes depuis 1970 ; `source` vaut `"ligne"` ou `"sonde"` ; une fenêtre absente vaut `null`. Écrit d'un coup (fichier temporaire puis remplacement).

## Le contrat entre la page et Python

**Python appelle** `window.recevoir(etat)` :

```json
{"etat": "ok", "message": null, "actualisation": false,
 "session": {"pourcentage": 49, "remise_a_zero": 1794528000, "echue": false},
 "semaine": {"pourcentage": 20, "remise_a_zero": 1794931200, "echue": false},
 "releve_a": 1794520000,
 "reglages": {"demarrage": true, "auto": false}}
```

- `etat` : `"ok"` (un relevé existe), `"vide"` (aucun relevé), `"erreur"` (la dernière actualisation a échoué : `message` dit pourquoi ; les fenêtres du dernier relevé restent données), `"absent"` (Claude Code introuvable).
- Une fenêtre dont l'heure de remise à zéro est passée est donnée avec `pourcentage: 0` et `echue: true`. Une fenêtre inconnue vaut `null`.
- La page met en forme les heures (« à 20:00 », « demain à 09:00 », « mardi à 17:00 », « dans 2 h 14 ») et l'âge du relevé ; elle les rafraîchit seule chaque minute.

**La page envoie** : `{action: "pret"}`, `{action: "actualiser"}`, `{action: "auto", on}`, `{action: "demarrage", on}`, `{action: "quitter"}`, `{action: "auteur"}`, et `{action: "hauteur", px}` quand la hauteur de son contenu change : le panneau n'a pas de hauteur fixe, la fenêtre s'y ajuste.

## Décisions, et pourquoi

1. **Jamais d'identifiant.** L'app ne lit ni le trousseau ni les fichiers de connexion de Claude Code. Les chiffres viennent de ce que Claude Code donne lui-même.
2. **Deux sources, une seule forme.** La ligne d'état (documentée, gratuite, mais muette quand Claude Code ne tourne pas) et la sonde (à la demande, non documentée, consomme un peu). `releve.py` traduit les deux ; le relevé le plus récent gagne.
3. **La sonde ne part jamais seule**, sauf si « Actualiser toutes les 15 minutes » est coché. Elle utilise le plus petit modèle, une réponse d'un mot, un dossier vide, et s'arrête au bout de 60 secondes.
4. **La ligne d'état ne casse pas celle de l'utilisateur.** S'il en a déjà une, l'installation la garde : `capture.py` note le relevé puis lance l'ancienne commande et rend sa sortie. Sinon, elle affiche « Session 49 % · Semaine 20 % ». `settings.json` est sauvegardé avant toute écriture, et seule la clé `statusLine` est touchée.
5. **Le temps fait partie de l'état.** Une fenêtre échue est remise à 0 % sans attendre un relevé : l'heure de remise à zéro est connue.
6. **Pas de réseau sur le fil principal** : la sonde tourne dans un fil à part ; l'app surveille le fichier de relevé toutes les deux secondes.
7. **Une seule app à la fois**, lancement à l'ouverture de session par un LaunchAgent, lanceur dans le dossier Applications : comme Hue Controller.

## Risques connus

| Risque | Parade |
| --- | --- |
| La forme de la réponse de la sonde change (elle n'est pas documentée) | Elle n'est qu'un complément ; l'app dit « Claude Code ne répond pas comme prévu. » et la ligne d'état continue de nourrir le relevé |
| Claude Code n'affiche pas la ligne d'état hors du terminal (application de bureau, extension) | La sonde reste disponible ; à vérifier à l'usage |
| Quelqu'un qui n'utilise que claude.ai | Hors périmètre (PRD) ; l'actualisation automatique couvre le cas si Claude Code est installé |
