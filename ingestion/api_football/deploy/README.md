# deploy
# API-Football : déploiement (bundle Databricks)

Bundle `api_football` → job **`JOB - API FOOTBALL - S2L2B`** (en dev : `[dev <utilisateur>] JOB - API FOOTBALL - S2L2B`).

## Fichiers
| Fichier | Rôle |
|---|---|
| `databricks.yml` | Racine : nom du bundle, fichiers synchronisés (`..` + `../../commun`), `include: bundle.*.yaml`, **cibles dev et prod** (l'éditeur de bundle ne lit les cibles que dans ce fichier) |
| `bundle.variables-customDefinition.yaml` | Variables : catalog, secret_scope, planification (06:00, en pause), seuil d'alerte (1 800 s) |
| `bundle.job_job_api_football_s2l2b.yaml` | Le job : paramètres, planification, alerte, 3 tâches |

## Le job (3 tâches)
```
run_api_football_initialisation → run_api_football_landing_loads → run_api_football_bronze_loads
   (commun/init_landing_bronze)      (fixtures, puis top*)            (fixtures, puis top*)
```
- Paramètres de job transmis à toutes les tâches : `CATALOG`, `SECRET_SCOPE` (clé `api-football-key`), `MODE_INIT=off`.
- Landing : 5 loaders dlthub en série (fixtures d'abord : les top* lisent la landing fixtures pour savoir si une saison est terminée).
- Bronze : 5 loaders COPY INTO (pas d'appel API, chaque fichier landing lu une seule fois).
- Dépendance dlthub : `dlt[parquet]==1.31.0` dans le panneau **Environment** du notebook `run_api_football_landing_loads`,
  **sans guillemets** ; aucun `%pip` dans les loaders.
- Alerte e-mail (adresse de la personne qui déploie) : échec, ou durée > 30 min.

## Quota de l'API (plan gratuit : 100 requêtes/jour, saisons 2022 à 2024)
- Incrémental : cellule 4 bis (fixtures) et 5 bis (top*) → un couple compétition × saison complet et terminé n'est **pas** rappelé.
- Run sans nouveauté = **0 requête**. Le compteur `/status` est en retard : garder une marge entre deux lancements.

## Dépendances
Le job **Open-Meteo** lit `bronze.api_football_fixtures` → il doit tourner **après** celui-ci (06:00 puis 07:00).

## Déployer (dev)
1. Ouvrir ce dossier dans l'éditeur de bundle (« Open in editor ») → panneau **🚀 Deployments**.
2. Target **dev** → **Deploy** → vérifier l'aperçu (créations / modifications / suppressions).
3. Jobs & Pipelines → le job → **Run now**.

- Mode dev « source-linked » : modifier un **notebook** ne demande pas de redéploiement ; modifier un **YAML**, si.
- Changer la **clé** du job dans le YAML = suppression + recréation du job (historique perdu).
- Ne jamais modifier le job dans l'interface : il est géré par le bundle.
- Le dossier `~/.bundle/api_football/dev/` du Home contient l'état du déploiement : ne pas le supprimer.

## Prod
Cible définie mais **pas encore déployée** : déploiement par `sp-data-prod` uniquement (CI/CD, étape 6), catalog `prod`, `scope-data-prod`.