# Transfermarkt : pas de job (choix assumé)

Source = fichiers plats **Kaggle** (dataset en pause depuis juillet 2026), chargés dans le Postgres Docker **du PC**
(`mds-postgres-1`, base `datalab`, schéma `transfermarkt`), puis envoyés en bronze par dlthub (recette C).

**Pourquoi pas de bundle ni de planification :**
- Databricks ne peut pas joindre le Postgres du PC → un job Databricks est impossible.
- La source ne change que lorsqu'on la recharge à la main → un job planifié tournerait pour rien,
  et players / clubs / competitions (photo complète) seraient ajoutées en double à chaque run.

## Procédure manuelle (à chaque nouvelle version Kaggle)
Prérequis : Docker Desktop démarré, `mds-postgres-1` prêt (`docker logs` → « ready to accept connections »),
`.venv` activé, `.dlt/secrets.toml` à la racine du dépôt (jamais dans Git).

1. Télécharger les CSV Kaggle dans `H:\projet-aws\donnees_kaggle\transfermarkt\` (hors dépôt).
2. Recharger le Postgres (mot de passe admin demandé à l'écran) :
   ```powershell
   # Options : voir --help (--dossier, --hote, --port, --base, --schema, --utilisateur)
   python ingestion/transfermarkt/utils/charger_kaggle_postgres.py --help
   ```
3. Charger le bronze (depuis la **racine du dépôt** : dlthub lit `.dlt\` dans le dossier courant) :
   ```powershell
   # Chargement normal (incrémental sur les tables d'historique)
   python ingestion/transfermarkt/process/03_bronze/01_loaders/transfermarkt_postgres_b_loader.py --catalog dev
   # Remise à zéro complète du bronze transfermarkt (si besoin)
   python ingestion/transfermarkt/process/03_bronze/01_loaders/transfermarkt_postgres_b_loader.py --catalog dev --reinitialiser
   ```
4. Contrôle : le loader affiche les lignes chargées par table (0 attendu sur les tables incrémentales en relance).