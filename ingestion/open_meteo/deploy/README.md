# Open-Meteo : déploiement (bundle Databricks)

Bundle `open_meteo` → job **`JOB - OPEN METEO - S2L2B`** (en dev : `[dev <utilisateur>] JOB - OPEN METEO - S2L2B`).

## Fichiers
| Fichier | Rôle |
|---|---|
| `databricks.yml` | Racine : nom du bundle, fichiers synchronisés (`..` + `../../commun`), `include: bundle.*.yaml`, **cibles dev et prod** (l'éditeur de bundle ne lit les cibles que dans ce fichier) |
| `bundle.variables-customDefinition.yaml` | Variables : catalog, secret_scope, planification (07:00, en pause), seuil d'alerte (2 700 s) |
| `bundle.job_job_open_meteo_s2l2b.yaml` | Le job : paramètres, planification, alerte, 3 tâches |

## Le job (3 tâches)
```
run_open_meteo_initialisation → run_open_meteo_landing_loads → run_open_meteo_bronze_loads
   (commun/init_landing_bronze)    (géocodage, puis météo)        (géocodage, puis météo)
```
- Paramètres de job transmis à toutes les tâches : `CATALOG`, `SECRET_SCOPE` (API sans clé, mais lu par les loaders), `MODE_INIT=off`.
- Les autres widgets des loaders gardent leur défaut : `VILLES` vide = toutes, `LOT_MAX` = 2000.
- Incrémental : les cellules 5 bis ne rappellent que les villes / jours absents de la landing.
- Alerte e-mail (adresse de la personne qui déploie) : échec, ou durée > 45 min.

## Dépendances (ordre de lancement)
- Le géocodage lit `bronze.api_football_fixtures` (villes des stades) → lancer **après** le job API-Football (planifié à 06:00, Open-Meteo à 07:00).
- La météo lit `bronze.api_football_fixtures` JOIN `bronze.open_meteo_geocodage` → une **nouvelle ville** n'a sa météo qu'au **run suivant** (le bronze géocodage est chargé après la landing). Choix assumé (calque S2L2B strict).

## Limites de l'API
600 appels/min, 5 000/h, 10 000/jour → `LOT_MAX` = 2000 et pause de 0,2 s entre appels. Ne pas lancer deux lots en moins d'une heure.

## Déployer (dev)
1. Ouvrir ce dossier dans l'éditeur de bundle (« Open in editor ») → panneau **🚀 Deployments**.
2. Target **dev** → **Deploy** → vérifier l'aperçu (créations / modifications / suppressions).
3. Jobs & Pipelines → le job → **Run now**.

- Mode dev « source-linked » : modifier un **notebook** ne demande pas de redéploiement ; modifier un **YAML**, si.
- Ne jamais modifier le job dans l'interface : il est géré par le bundle.
- Le dossier `~/.bundle/open_meteo/dev/` du Home contient l'état du déploiement : ne pas le supprimer.

## Prod
Cible définie mais **pas encore déployée** : déploiement par `sp-data-prod` uniquement (CI/CD, étape 6), catalog `prod`, `scope-data-prod`.