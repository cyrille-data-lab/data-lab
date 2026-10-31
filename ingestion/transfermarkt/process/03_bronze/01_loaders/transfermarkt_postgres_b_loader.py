"""
transfermarkt_postgres_b_loader.py  (v2 - étape 3.7)
----------------------------------------------------
Charge les tables Transfermarkt du Postgres local (schéma transfermarkt)
vers <catalog>.bronze avec dlthub.
Trajet : Postgres (rôle dlt_reader) -> volume <catalog>.landing.dlt_staging (transit Parquet)
         -> tables <catalog>.bronze.transfermarkt_<table> (COPY INTO fait par dlthub).
 
Modes de chargement (décisions 3.7) :
  - player_valuations : incrémental sur "date"           -> seules les lignes nouvelles sont ajoutées
  - transfers         : incrémental sur "transfer_date"  -> idem ; lignes sans date conservées
  - players, clubs, competitions : photo complète ajoutée à chaque dépôt (append)
  Le bronze garde tous les dépôts ; le silver dédoublonnera.
 
Identifiants : .dlt/secrets.toml à la racine du dépôt (jamais dans le code, jamais dans Git).
 
Usage (depuis la racine du dépôt, venv activé) :
    Chargement normal :
        python ingestion/transfermarkt/process/03_bronze/01_loaders/transfermarkt_postgres_b_loader.py --catalog dev
    Remise à zéro (supprime les tables bronze transfermarkt et l'état incrémental, puis recharge tout) :
        python ingestion/transfermarkt/process/03_bronze/01_loaders/transfermarkt_postgres_b_loader.py --catalog dev --reinitialiser
"""
import argparse
import os
 
# Paramètres dlthub fixés AVANT l'import de dlt
os.environ.setdefault("RUNTIME__DLTHUB_TELEMETRY", "false")                      # pas de télémétrie
os.environ.setdefault("NORMALIZE__PARQUET_NORMALIZER__ADD_DLT_LOAD_ID", "true")  # ajoute _dlt_load_id (=> _date_depot en silver)
 
import dlt
from dlt.sources.sql_database import sql_database
 
SOURCE = "transfermarkt"                       # préfixe des tables bronze (convention <source>_<table>)
TABLES = ["competitions", "clubs", "players", "player_valuations", "transfers"]
 
# Tables d'historique chargées en incrémental : table -> (colonne curseur, que faire des lignes sans date)
INCREMENTAL = {
    "player_valuations": ("date", "raise"),       # date toujours renseignée : une ligne vide = anomalie -> arrêt
    "transfers": ("transfer_date", "include"),    # quelques dates vides possibles : on les garde
}
 
# Types imposés : colonnes que dlthub ne peut pas typer seul (vides à 100 % dans la source, cf. diagnostic 3.7-A)
TYPES_IMPOSES = {
    "clubs": {"total_market_value": {"data_type": "double", "nullable": True}},
}
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="Postgres transfermarkt -> <catalog>.bronze (dlthub)")
    parser.add_argument("--catalog", default="dev", help="Catalog Unity Catalog cible (dev ou prod)")
    parser.add_argument("--schema-source", default="transfermarkt", help="Schéma Postgres à lire")
    parser.add_argument("--reinitialiser", action="store_true",
                        help="Supprime les tables bronze de la source et l'état incrémental, puis recharge tout")
    args = parser.parse_args()
 
    # Garde-fou : le catalog demandé doit être celui des identifiants de secrets.toml
    catalog_secrets = dlt.secrets["destination.databricks.credentials.catalog"]
    if catalog_secrets != args.catalog:
        raise SystemExit(f"❌ --catalog={args.catalog} mais secrets.toml pointe sur '{catalog_secrets}'. Arrêt.")
 
    # Source : les 5 tables du schéma Postgres, lues en Arrow (rapide)
    source = sql_database(schema=args.schema_source, table_names=TABLES, backend="pyarrow")
    for table in TABLES:
        ressource = source.resources[table]
        # Renommage bronze (transfermarkt_<table>) + append : on garde tous les dépôts
        ressource.apply_hints(table_name=f"{SOURCE}_{table}", write_disposition="append")
        if table in TYPES_IMPOSES:
            ressource.apply_hints(columns=TYPES_IMPOSES[table])
        if table in INCREMENTAL:
            colonne, si_vide = INCREMENTAL[table]
            # dlthub mémorise la plus grande valeur chargée et ne lit ensuite que les lignes >= à cette valeur
            ressource.apply_hints(incremental=dlt.sources.incremental(colonne, on_cursor_value_missing=si_vide))
 
    # Destination : Databricks, fichiers en transit dans le volume landing.dlt_staging
    destination = dlt.destinations.databricks(staging_volume_name=f"{args.catalog}.landing.dlt_staging")
 
    pipeline = dlt.pipeline(
        pipeline_name="transfermarkt_postgres_bronze",
        destination=destination,
        dataset_name="bronze",                 # schéma cible : <catalog>.bronze
    )
 
    if args.reinitialiser:
        print("⚠️  Remise à zéro : les tables bronze transfermarkt_* et l'état incrémental vont être supprimés.")
        info = pipeline.run(source, refresh="drop_sources")
    else:
        info = pipeline.run(source)
    info.raise_on_failed_jobs()                # échec explicite si un fichier n'a pas été chargé
 
    if not info.loads_ids:
        print("ℹ️  Aucune donnée nouvelle : rien n'a été chargé.")
        return
    load_id = info.loads_ids[0]
    print(f"✅ Chargement terminé (load_id = {load_id})")
 
    # Contrôle : lignes chargées par CE dépôt, table par table (0 attendu sur une relance en incrémental)
    with pipeline.sql_client() as client:
        for table in TABLES:
            nom = client.make_qualified_table_name(f"{SOURCE}_{table}")
            n = client.execute_sql(f"SELECT COUNT(*) FROM {nom} WHERE _dlt_load_id = '{load_id}'")[0][0]
            mode = "incrémental" if table in INCREMENTAL else "photo complète"
            print(f"   {nom:<60} {n:>10,} lignes  ({mode})".replace(",", " "))
    print("🏁 Bronze transfermarkt à jour.")
 
 
if __name__ == "__main__":
    main()