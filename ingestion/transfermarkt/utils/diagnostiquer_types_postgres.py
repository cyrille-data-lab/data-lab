"""
diagnostiquer_types_postgres.py
-------------------------------
Outil de diagnostic, sans écriture : pour chaque table d'un schéma Postgres, affiche
  - le type de chaque colonne tel que SQLAlchemy le lit (c'est ce que dlthub reçoit) ;
  - les types NON reconnus (NullType) : dlthub doit alors deviner le type à partir des données ;
  - les colonnes vides à 100 % : sans type reconnu, dlthub ne les crée pas à destination.
 
Identifiants : section [sources.sql_database.credentials] de .dlt/secrets.toml (rien dans le code).
 
Usage (depuis la racine du dépôt, venv activé) :
    python ingestion/transfermarkt/utils/diagnostiquer_types_postgres.py --schema transfermarkt
"""
import argparse
import os
 
os.environ.setdefault("RUNTIME__DLTHUB_TELEMETRY", "false")   # pas de télémétrie dlthub
 
import dlt
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.types import NullType
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostic des types Postgres vus par dlthub")
    parser.add_argument("--schema", default="transfermarkt", help="Schéma Postgres à analyser")
    args = parser.parse_args()
 
    # Connexion avec les identifiants de secrets.toml (compte lecture seule dlt_reader)
    cr = dlt.secrets["sources.sql_database.credentials"]
    url = URL.create(
        cr["drivername"], username=cr["username"], password=cr["password"],
        host=cr["host"], port=int(cr["port"]), database=cr["database"],
    )
    moteur = create_engine(url)
    inspecteur = inspect(moteur)
 
    types_inconnus, colonnes_vides = [], []
 
    with moteur.connect() as cx:
        for table in sorted(inspecteur.get_table_names(schema=args.schema)):
            colonnes = inspecteur.get_columns(table, schema=args.schema)
 
            # Une seule requête par table : nombre de lignes + nombre de valeurs non vides par colonne
            comptes = ", ".join(f'count("{c["name"]}")' for c in colonnes)
            resultat = cx.execute(text(f'SELECT count(*), {comptes} FROM "{args.schema}"."{table}"')).one()
            total, non_vides = resultat[0], resultat[1:]
 
            print(f"\n=== {args.schema}.{table} ({total:,} lignes) ===".replace(",", " "))
            for col, n in zip(colonnes, non_vides):
                t = col["type"]
                inconnu = isinstance(t, NullType)
                vide = total > 0 and n == 0
                libelle = "?" if inconnu else str(t)
                alertes = ("  ⚠️ TYPE NON RECONNU" if inconnu else "") + ("  ⚠️ VIDE À 100 %" if vide else "")
                print(f"   {col['name']:<40} {libelle:<18} ({type(t).__name__}){alertes}")
                if inconnu:
                    types_inconnus.append(f"{table}.{col['name']}")
                if vide:
                    colonnes_vides.append(f"{table}.{col['name']} ({libelle})")
 
    print("\n--- Synthèse ---")
    print(f"Types non reconnus : {types_inconnus or 'aucun'}")
    print(f"Colonnes vides à 100 % : {colonnes_vides or 'aucune'}")
 
 
if __name__ == "__main__":
    main()
 