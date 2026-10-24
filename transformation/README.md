# transformation

Projet **dbt** : transforme les données Bronze en couches **Silver** et **Gold** dans Databricks.

- Cibles dbt `dev` et `prod` : le catalog est passé en variable, jamais écrit en dur.
- Fichiers générés (`target/`, `dbt_packages/`, `logs/`) ignorés par Git.

Contenu ajouté à l'étape 4.
