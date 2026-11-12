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

## Écarté

Lire les identifiants de Claude Code dans le trousseau pour interroger directement Anthropic : c'est manipuler un
secret pour une information que Claude Code donne déjà.
