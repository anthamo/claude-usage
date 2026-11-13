# Essai du 12/11/2026 : d'où tirer la consommation

Deux sources, toutes deux fournies par Claude Code lui-même, sans lire aucun identifiant.

## 1. La ligne d'état (documentée)

Claude Code passe à la commande `statusLine` un JSON qui contient, pour un abonné Pro, Max ou Ultra et après la
première réponse de la session :

    "rate_limits": {
      "five_hour": {"used_percentage": 23.5, "resets_at": 1738425600},
      "seven_day": {"used_percentage": 41.2, "resets_at": 1738857600}
    }

`used_percentage` va de 0 à 100, `resets_at` est en secondes depuis 1970. Chaque fenêtre peut manquer.
Source : https://code.claude.com/docs/en/statusline (lue le 12/11/2026).

## 2. Une question posée sans interface (constatée, non documentée)

`claude -p "ok" --model haiku --output-format stream-json --verbose --max-turns 1` émet, parmi ses lignes :

    {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "resetsAt": 1794528000,
     "rateLimitType": "five_hour", "unifiedWindows": {
       "five_hour": {"utilization": 0.49, "resetsAt": 1794528000, "status": "allowed"},
       "seven_day": {"utilization": 0.2, "resetsAt": 1794931200, "status": "allowed"}}}}

`utilization` va de 0 à 1. Constaté avec Claude Code 2.1.322. Cette forme n'est pas documentée : elle peut changer.
Chaque appel consomme une toute petite part de l'abonnement.

Mesuré le 13/11/2026 sur un appel : environ 19 000 jetons, presque tous d'instructions de Claude Code mises en
cache, 92 jetons de réponse, 1,3 seconde, soit 0,002 $ au tarif public. Toutes les 15 minutes sur une journée
entière, cela fait une centaine d'appels et environ 0,20 $ d'équivalent : négligeable devant un abonnement.

## Écarté

Lire les identifiants de Claude Code dans le trousseau pour interroger directement Anthropic : c'est manipuler un
secret pour une information que Claude Code donne déjà.

## Ce que la sonde pèse dans l'abonnement (estimé le 13/11/2026)

Méthode : chiffrer au tarif public la consommation des journaux locaux de Claude Code, la rapporter aux pourcentages
de session et de semaine affichés au même moment, et en tirer ce que vaut un point de pourcentage. Résultat : une sonde
(0,002 $) pèse environ 0,007 % d'une session ; toutes les 15 minutes, 0,13 % d'une session de 5 heures et 0,4 % de la
semaine. Ordre de grandeur seulement : il dépend de la formule d'abonnement, et l'estimation de session
repose sur dix minutes de données.
