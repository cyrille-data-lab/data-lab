# data-lab

Data Lab – dlthub, dbt, Databricks, AWS.

Projet data organisé comme un projet d'entreprise : ingestion avec **dlthub**, transformations avec **dbt**, exécution sur **Databricks**, CI/CD sur **AWS**.

## Architecture

```
Sources (API, bases)
   │  dlthub
   ▼
Bronze  ──dbt──▶  Silver  ──dbt──▶  Gold
        (catalog dev ou prod, Databricks Unity Catalog)
```

## Environnements

| Environnement | Workspace Databricks | Catalog | Qui écrit |
|---|---|---|---|
| dev | `dbx-dev` | `dev` | Les développeurs (`grp-data-engineers`) et `sp-data-dev` |
| prod | `dbx-prod` | `prod` | Uniquement `sp-data-prod`, via la CI/CD |

Aucun développement en prod. La prod reçoit uniquement le code validé de `main`.

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `ingestion/` | Pipelines dlthub (sources → Bronze) |
| `transformation/` | Projet dbt (Silver et Gold) |
| `resources/` | Jobs et pipelines Databricks (bundle) |
| `ci/` | CI/CD AWS (CodeBuild, CodePipeline) |
| `docs/` | Manuels et schémas du projet |

## Règles de travail

1. Créer une branche depuis `main` : `feature/<sujet>`.
2. Développer et tester dans `dbx-dev`.
3. Commit, push, puis Pull Request vers `main`.
4. La CI vérifie la PR ; merge en **Squash** (1 PR = 1 commit).
5. Le merge dans `main` déclenche le déploiement en prod.

- Push direct sur `main` interdit (branche protégée).
- Aucune valeur en dur : noms de catalogs, hôtes et identifiants passent par des variables.
- Aucun secret dans le dépôt : les secrets sont dans AWS Secrets Manager.
