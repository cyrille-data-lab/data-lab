# ingestion

Pipelines **dlthub** : récupèrent les données des sources (API, bases) et les déposent dans la couche **Bronze** de Databricks.

- Destination : schéma `bronze` du catalog de l'environnement (`dev` ou `prod`), passé en variable.
- Secrets (clés d'API, mots de passe) : jamais dans le dépôt. En local dans `.dlt/secrets.toml` (ignoré par Git), en dev/prod dans AWS Secrets Manager.

Contenu ajouté à l'étape 3.
