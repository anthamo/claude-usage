# PRD : la consommation de l'abonnement Claude dans la barre de menus

## 1. Le problème

**Quel problème.** On ne voit où on en est de son abonnement Claude qu'en ouvrant la page d'usage, ou quand la limite tombe, souvent en plein travail et sans prévenir.

**Pourquoi.**
- La limite de session se remet à zéro toutes les cinq heures, celle de la semaine tous les sept jours : savoir où on en est change ce qu'on lance (une grosse tâche maintenant, ou après la remise à zéro).
- Claude Code fournit ces chiffres lui-même (`essais/sonde.md`) : pas besoin de manipuler un mot de passe.

**Cible.** Une personne abonnée à Claude (Pro, Max), avec Claude Code installé et connecté sur son Mac.

**Condition de succès.**
- Le pourcentage de la session se lit dans la barre de menus, sans cliquer.
- Le panneau montre ce que montre la page d'usage de Claude : session actuelle et semaine, chacune avec son pourcentage et l'heure de sa remise à zéro.
- Signal d'échec : si l'on se fait encore surprendre par la limite, l'app ne remplit pas son rôle.

## 2. La solution

**Description.** Une icône et un pourcentage dans la barre de menus. Un clic ouvre un panneau avec deux cartes, comme la page d'usage :

```
                              [icône] 49 %    son  wifi  heure
        +---------------------------------------+
        |  Claude                       ( roue ) |
        |  Relevé il y a 3 min · Actualiser      |
        |                                        |
        |  SESSION ACTUELLE                49 %  |
        |  [##########------------]              |
        |  Remise à zéro à 20:00 · dans 2 h 14   |
        |                                        |
        |  CETTE SEMAINE                   20 %  |
        |  [####------------------]              |
        |  Remise à zéro mardi à 17:00           |
        +---------------------------------------+
```

**D'où viennent les chiffres.**
1. **En continu et sans rien coûter** : chaque fois que Claude Code tourne dans un terminal, il donne les deux pourcentages à sa ligne d'état. L'app installe une ligne d'état qui les note au passage.
2. **À la demande** : le bouton « Actualiser » pose une question d'un mot à Claude et lit les pourcentages dans la réponse. Chaque actualisation consomme une toute petite part de l'abonnement ; elle n'est donc jamais faite en cachette, sauf si on coche « Actualiser toutes les 15 minutes » dans les réglages (décoché au départ). Dans ce cas, la première part dès le lancement de l'app.

**Se connecter à Claude** : l'app n'a pas de connexion à elle. Elle passe par Claude Code, déjà installé et connecté sur le Mac. Aucun identifiant n'est lu, copié ni gardé par l'app.

**Ce qu'on ne traite pas.**
- La consommation par modèle, le détail par conversation, l'historique.
- Les notifications à l'approche de la limite (candidat pour la suite).
- Un Mac sans Claude Code : il faut l'installer et s'y connecter, même si l'on n'utilise que l'app Claude.
- Les crédits supplémentaires et la facturation à l'usage.

**Proposition de valeur.** Savoir où on en est avant de lancer, sans y penser.

## 3. Décisions

| # | Question | Décision |
| --- | --- | --- |
| 1 | Source des chiffres | Claude Code, par sa ligne d'état et par une question d'un mot. Jamais les identifiants. |
| 2 | Ce que montre la barre de menus | Le pourcentage de la session : c'est lui qui bloque en plein travail. |
| 3 | Couleur | La couleur d'accent du Mac jusqu'à 74 %, orange de 75 à 89 %, rouge à partir de 90 %. |
| 4 | Fenêtre dont l'heure de remise à zéro est passée | Affichée à 0 %, « Remise à zéro faite », jusqu'au relevé suivant. |
| 5 | Actualisation automatique | Décochée au départ : elle consomme un peu. |
| 6 | Direction visuelle | Natif, comme [Hue Controller](https://github.com/anthamo/hue-controller) : le panneau ressemble à un réglage du Mac. Règles dans `DESIGN.md`. |
| 7 | Technique | Le socle de Hue Controller : Python (PyObjC), page HTML dans un panneau en verre. |
