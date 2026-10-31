"""
transfermarkt_postgres_b_loader.py
----------------------------------
Charge les tables Transfermarkt du Postgres local (schéma transfermarkt)
vers <catalog>.bronze avec dlthub.
Trajet : Postgres (rôle dlt_reader) -> volume <catalog>.landing.dlt_staging (transit Parquet)
         -> tables <catalog>.bronze.transfermarkt_<table> (COPY INTO fait par dlthub).
 
Identifiants : .dlt/secrets.toml à la racine du dépôt (jamais dans le code, jamais dans Git).
 
Usage (depuis la racine du dépôt, venv activé) :
    python ingestion/transfermarkt/process/03_bronze/01_loaders/transfermarkt_postgres_b_loader.py --catalog dev
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
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="Postgres transfermarkt -> <catalog>.bronze (dlthub)")
    parser.add_argument("--catalog", default="dev", help="Catalog Unity Catalog cible (dev ou prod)")
    parser.add_argument("--schema-source", default="transfermarkt", help="Schéma Postgres à lire")
    args = parser.parse_args()
 
    # Garde-fou : le catalog demandé doit être celui des identifiants de secrets.toml
    catalog_secrets = dlt.secrets["destination.databricks.credentials.catalog"]
    if catalog_secrets != args.catalog:
        raise SystemExit(f"❌ --catalog={args.catalog} mais secrets.toml pointe sur '{catalog_secrets}'. Arrêt.")
 
    # Source : les 5 tables du schéma Postgres, lues en Arrow (rapide)
    source = sql_database(schema=args.schema_source, table_names=TABLES, backend="pyarrow")
    for table in TABLES:
        # Renommage bronze (transfermarkt_<table>) + append : on garde tous les dépôts
        source.resources[table].apply_hints(table_name=f"{SOURCE}_{table}", write_disposition="append")
 
    # Destination : Databricks, fichiers en transit dans le volume landing.dlt_staging
    destination = dlt.destinations.databricks(staging_volume_name=f"{args.catalog}.landing.dlt_staging")
 
    pipeline = dlt.pipeline(
        pipeline_name="transfermarkt_postgres_bronze",
        destination=destination,
        dataset_name="bronze",                 # schéma cible : <catalog>.bronze
    )
 
    info = pipeline.run(source)
    info.raise_on_failed_jobs()                # échec explicite si un fichier n'a pas été chargé
    load_id = info.loads_ids[0]
    print(f"✅ Chargement terminé (load_id = {load_id})")
 
    # Contrôle : lignes chargées par CE dépôt, table par table
    with pipeline.sql_client() as client:
        for table in TABLES:
            nom = client.make_qualified_table_name(f"{SOURCE}_{table}")
            n = client.execute_sql(f"SELECT COUNT(*) FROM {nom} WHERE _dlt_load_id = '{load_id}'")[0][0]
            print(f"   {nom:<60} {n:>10,} lignes".replace(",", " "))
    print("🏁 Bronze transfermarkt à jour.")
 
 
if __name__ == "__main__":
    main()
 