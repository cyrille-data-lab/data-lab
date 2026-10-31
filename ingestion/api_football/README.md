# Source : API-Football (api-sports.io)

Données de football : compétitions, saisons, matchs, événements (buts, cartons), arbitres.

- Mode d'exécution : dlthub sur Databricks (notebook serverless, puis job à l'étape 5).
- Trajet : API → `landing.files/api_football/<table>/<aaaa>/<mm>/<jj>/` (date du dépôt) → tables `bronze.api_football_*`.
- Accès : plan Free, 100 requêtes/jour, saisons 2022 à 2024 (2025-2026 via un mois payant plus tard).
- Clé API : secret, jamais dans le code (secret scope Databricks).
