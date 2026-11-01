# Source : Open-Meteo a 2 API,

- geocoding-api.open-meteo.com (ville → coordonnées) → table geocodage
- archive-api.open-meteo.com (météo historique) → table à venir
Données de météo : par villes et par pays seront croisées avec le calendrier des matchs

- Mode d'exécution : dlthub sur Databricks (notebook serverless, puis job à l'étape 5).
- Trajet : API → `landing.files/open_meteo/<table>/<aaaa>/<mm>/<jj>/` (date du dépôt) → tables `bronze.open_meteo_*`.
- Accès : plan Free, .
- Clé API : aucune.
