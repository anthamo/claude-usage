# DESIGN : Claude Usage

Direction **Natif**, reprise de Hue Controller (`../hue-controller/DESIGN.md`, qui fait foi pour tout ce qui n'est pas redit ici) : un panneau en verre de macOS 26, la police du système, la couleur d'accent du Mac, le mode clair et le mode sombre.

## Direction, en cinq lignes

1. **Produit.** Une jauge dans la barre de menus et un panneau dessous, pour savoir où en est l'abonnement Claude avant de lancer une tâche.
2. **Caractère.** Sobre, lisible d'un coup d'œil, sans alarme inutile.
3. **Univers.** Les jauges du Mac : batterie, stockage.
4. **Où vit la couleur.** Dans les deux barres, et seulement là. Elle dit un état : accent jusqu'à 74 %, orange de 75 à 89 %, rouge à partir de 90 %.
5. **Signature.** Le pourcentage dans la barre de menus : l'information est lue sans ouvrir l'app.

## Barre de menus

Une jauge (symbole du système, dont l'aiguille monte par paliers) suivie du pourcentage de la session, « 49 % ». Sans relevé : la jauge seule. À partir de 90 % : le pourcentage en rouge.

## Structure du panneau (360 px de large, hauteur selon le contenu)

1. **En-tête** : « Claude » (20 px gras) ; dessous, en secondaire, l'âge du relevé et le lien « Actualiser » (« Relevé il y a 3 min · Actualiser » ; pendant l'actualisation : « Actualisation… »). À droite, la roue dentée des réglages.
2. **Deux cartes** (tuile, rayon 8), une par fenêtre, « Session actuelle » puis « Cette semaine ». Dans chaque carte, de haut en bas :
   - le titre de section (11 px, capitales espacées, gris) et, sur la même ligne à droite, le pourcentage (« 49 % », 16 px gras, chiffres à chasse fixe, à la couleur de l'état quand il est orange ou rouge) ;
   - la barre : 8 px de haut, rayon 4, fond « piste », remplie à la couleur de l'état ;
   - une ligne en secondaire : « Remise à zéro à 20:00 · dans 2 h 14 » (le jour même), « Remise à zéro demain à 09:00 » (suivi de « · dans 2 h 05 » si c'est dans moins de douze heures), « Remise à zéro mardi à 17:00 » ; fenêtre échue : « Remise à zéro faite » ; fenêtre absente : « Pas encore de relevé ».
3. **Réglages** (la roue remplace les cartes) : « Lancer à l'ouverture de session » (interrupteur) ; « Actualiser toutes les 15 minutes » (interrupteur) avec dessous, en secondaire, « Chaque actualisation consomme un peu de l'abonnement. » ; « Quitter Claude Usage » (carte cliquable avec le pictogramme marche/arrêt) ; en bas, la signature « Application créée par Anthony Hamo » (lien) et « Terminé ».

## États

| État | Ce qu'on voit |
| --- | --- |
| Pas encore de relevé | Les deux cartes avec une barre vide et « Pas encore de relevé » ; sous le titre : « Aucun relevé · Actualiser » |
| Actualisation en cours | « Actualisation… » ; le lien est inactif |
| Actualisation en échec | Sous le titre, la phrase d'erreur (« Claude Code ne répond pas. ») puis « · Réessayer » |
| Claude Code introuvable | « Claude Code n'est pas installé sur ce Mac. » sans lien |

## Couleurs d'état (en plus de la table de Hue Controller)

| Rôle | Clair | Sombre |
| --- | --- | --- |
| Normal (jusqu'à 74 %) | la couleur d'accent du Mac | idem |
| Attention (75 à 89 %) | `#c96a00` | `#ff9f0a` |
| Limite (90 % et plus) | `#d70015` | `#ff453a` |
