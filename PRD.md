# PRD : la consommation de l'abonnement Claude dans la barre de menus

Écrit le 12/11/2026. Projet mené en autonomie à la demande d'Antho : les hypothèses et les choix sont de Claude, et marqués comme tels.

## 1. Le problème

**Quel problème.** Antho ne voit où il en est de son abonnement Claude qu'en ouvrant la page d'usage, ou quand la limite tombe. Le jour de l'écriture de ce PRD, la session est arrivée à 100 % en plein travail, deux fois, sans prévenir.

**Pourquoi vrai et pourquoi maintenant.**
- La limite de session se remet à zéro toutes les cinq heures, celle de la semaine tous les sept jours : savoir où on en est change ce qu'on lance (une grosse tâche maintenant, ou après la remise à zéro).
- Claude Code fournit ces chiffres lui-même (essai du 12/11, `essais/sonde.md`) : pas besoin de manipuler un mot de passe.
- Le socle existe : Hue Controller a montré la forme (icône, panneau en verre, page) et la méthode.

**Cibles.** Antho, sur son Mac. Puis sa compagne, sur le sien, avec son propre abonnement.

**Condition de succès.**
- Le pourcentage de la session se lit dans la barre de menus, sans cliquer.
- Le panneau montre ce que montre la page d'usage de Claude : session actuelle et semaine, chacune avec son pourcentage et l'heure de sa remise à zéro.
- Signal d'arrêt : si, après deux semaines, Antho se fait encore surprendre par la limite, l'app ne remplit pas son rôle (hypothèse de Claude).

## 2. La solution

**Description.** Une jauge et un pourcentage dans la barre de menus. Un clic ouvre un panneau avec deux lignes, comme la page d'usage :

```
                              [jauge] 49 %    son  wifi  heure
        +---------------------------------------+
        |  Claude                       ( roue ) |
        |  Relevé il y a 3 min · Actualiser      |
        |                                        |
        |  SESSION ACTUELLE                      |
        |  [##########------------]   49 %       |
        |  Remise à zéro à 20:00 · dans 2 h 14   |
        |                                        |
        |  CETTE SEMAINE                         |
        |  [####------------------]   20 %       |
        |  Remise à zéro mardi à 17:00           |
        +---------------------------------------+
```

**D'où viennent les chiffres** (choix de Claude) :
1. **En continu et sans rien coûter** : chaque fois que Claude Code tourne dans un terminal, il donne les deux pourcentages à sa ligne d'état. L'app installe une ligne d'état qui les note au passage.
2. **À la demande** : le bouton « Actualiser » pose une question d'un mot à Claude et lit les pourcentages dans la réponse. Chaque actualisation consomme une toute petite part de l'abonnement ; elle n'est donc jamais faite en cachette, sauf si on coche « Actualiser toutes les 15 minutes » dans les réglages (décoché au départ).

**Se connecter à Claude** : l'app n'a pas de connexion à elle. Elle passe par Claude Code, déjà installé et connecté sur le Mac (c'est aussi lui qui fait l'installation). Aucun identifiant n'est lu, copié ni gardé par l'app.

**Ce qu'on ne traite pas.**
- La consommation par modèle, le détail par conversation, l'historique.
- Les notifications à l'approche de la limite (candidat pour la suite).
- Un compte qui n'utilise que claude.ai, sans Claude Code installé.
- Les crédits supplémentaires et la facturation à l'usage.

**Proposition de valeur.** Savoir où on en est avant de lancer, sans y penser.

**Rollout.** Sur le Mac d'Antho d'abord. Sur le second Mac ensuite, par la consigne d'installation à coller dans Claude Code.

## 3. Décisions

| # | Question | Décision (de Claude, sauf mention) |
| --- | --- | --- |
| 1 | Source des chiffres | Claude Code, par sa ligne d'état et par une question d'un mot. Jamais les identifiants. |
| 2 | Ce que montre la barre de menus | Le pourcentage de la session : c'est lui qui bloque en plein travail. |
| 3 | Couleur | La couleur d'accent du Mac jusqu'à 74 %, orange de 75 à 89 %, rouge à partir de 90 %. |
| 4 | Fenêtre dont l'heure de remise à zéro est passée | Affichée à 0 %, « remise à zéro », jusqu'au relevé suivant. |
| 5 | Actualisation automatique | Décochée au départ : elle consomme un peu. |
| 6 | Direction visuelle | Celle de Hue Controller (Natif) : `DESIGN.md` en reprend les règles. |
| 7 | Nom | Dossier `claude-usage`, application « Claude Usage ». |
| 8 | Technique | Celle de Hue Controller : Python (PyObjC), page HTML dans un panneau en verre. |
