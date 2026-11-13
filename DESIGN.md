# DESIGN : Claude Usage

Direction **Natif**, la même que [Hue Controller](https://github.com/anthamo/hue-controller) : un panneau en verre de macOS 26, la police du système, la couleur d'accent du Mac, le mode clair et le mode sombre. La référence, c'est la page elle-même : `open claude_usage/panneau/index.html` l'ouvre dans un navigateur sur un faux relevé.

## Direction, en cinq lignes

1. **Produit.** Une icône et un pourcentage dans la barre de menus, un panneau dessous, pour savoir où en est l'abonnement Claude avant de lancer une tâche.
2. **Caractère.** Sobre, lisible d'un coup d'œil, sans alarme inutile.
3. **Univers.** Les jauges du Mac : batterie, stockage.
4. **Où vit la couleur.** Dans les deux barres, et seulement là. Elle dit un état : accent jusqu'à 74 %, orange de 75 à 89 %, rouge à partir de 90 %.
5. **Signature.** Le pourcentage dans la barre de menus : l'information se lit sans ouvrir l'app.

## Barre de menus

L'icône (un astérisque dans un cadran, `claude_usage/barre.png`), suivie du pourcentage de la session, « 49 % ». Sans relevé : l'icône seule. À partir de 90 % : le pourcentage en rouge. L'icône est une image « modèle » : macOS la teint en noir ou en blanc selon la barre. Elle est fixe : c'est le pourcentage qui dit le niveau.

**Icône de l'application** : le cadran en couleur de `design/icone/app.png`, mis en forme par `outils/icone.py` (forme arrondie du Mac, coins transparents) et copié dans le lanceur.

## Structure du panneau (360 px de large, hauteur selon le contenu)

1. **En-tête** : « Claude » (20 px gras) ; dessous, en secondaire, l'âge du relevé et le lien « Actualiser » (« Relevé il y a 3 min · Actualiser » ; pendant l'actualisation : « Actualisation… »). À droite, la roue dentée des réglages.
2. **Deux cartes** (tuile, rayon 8), une par fenêtre, « Session actuelle » puis « Cette semaine ». Dans chaque carte, de haut en bas :
   - le titre de section (11 px, capitales espacées, gris) et, sur la même ligne à droite, le pourcentage (« 49 % », 16 px gras, chiffres à chasse fixe, à la couleur de l'état quand il est orange ou rouge) ;
   - la barre : 8 px de haut, rayon 4, fond « piste », remplie à la couleur de l'état ;
   - une ligne en secondaire : « Remise à zéro à 20:00 · dans 2 h 14 » (le jour même), « Remise à zéro demain à 09:00 » (suivi de « · dans 2 h 05 » si c'est dans moins de douze heures), « Remise à zéro mardi à 17:00 » ; fenêtre échue : « Remise à zéro faite » ; fenêtre absente : « Pas encore de relevé ».
3. **Réglages** (la roue remplace les cartes) : « Lancer à l'ouverture de session » (interrupteur) ; « Actualiser toutes les 15 minutes » (interrupteur) avec dessous, en secondaire, « Chaque actualisation consomme un peu de l'abonnement. » ; « Quitter Claude Usage » (carte cliquable avec le pictogramme marche/arrêt : en texte seul, on le prendrait pour un libellé) ; en bas, le nom de l'auteur (lien vers sa page GitHub) et « Terminé ».

## États

| État | Ce qu'on voit |
| --- | --- |
| Pas encore de relevé | Les deux cartes avec une barre vide et « Pas encore de relevé » ; sous le titre : « Aucun relevé · Actualiser » |
| Actualisation en cours | « Actualisation… » ; le lien est inactif |
| Actualisation en échec | Sous le titre, la phrase d'erreur (« Claude Code ne répond pas. ») puis « · Réessayer » |
| Claude Code introuvable | « Claude Code n'est pas installé sur ce Mac. » sans lien |

## Couleurs

Le fond est le verre des panneaux de la barre de menus de macOS 26 ; la page est transparente.

| Rôle | Clair | Sombre |
| --- | --- | --- |
| Texte | `#1d1d1f` | `#f5f5f7` |
| Texte secondaire | `#5c5c61` | `rgba(255,255,255,.62)` |
| Creux (survol) | `rgba(0,0,0,.07)` | `rgba(255,255,255,.08)` |
| Tuile, carte | `rgba(255,255,255,.74)` | `rgba(255,255,255,.1)` |
| Surface en avant (survol d'une carte cliquable) | `#fff` | `rgba(255,255,255,.2)` |
| Filets | `rgba(0,0,0,.1)` | `rgba(255,255,255,.12)` |
| Piste vide d'une barre | `rgba(0,0,0,.14)` | `rgba(255,255,255,.2)` |
| Interrupteur éteint | `rgba(0,0,0,.18)` | `rgba(255,255,255,.2)` |
| Normal (jusqu'à 74 %), interrupteur allumé | la couleur d'accent du Mac ; `#34c759` dans un navigateur | idem |
| Attention (75 à 89 %) | `#c96a00` | `#ff9f0a` |
| Limite (90 % et plus) | `#d70015` | `#ff453a` |

## Règles

Celles de Hue Controller : grille de 4 px, rayons 20 (panneau) et 8 (cartes), police du système, chiffres à chasse fixe, pas d'infobulle, pas de cadre dans un cadre, pas de couleur décorative.
