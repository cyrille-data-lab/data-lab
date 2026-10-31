"""
Chargement des fichiers Kaggle « Football Data from Transfermarkt » (auteur : dcaribou)
dans la base Postgres locale du Data Lab : datalab.transfermarkt.

Rôle dans le projet
-------------------
Ce script joue le rôle de l'« application métier » qui alimente la base source
(l'équivalent du SQL Server en entreprise). Il est lancé À LA MAIN, sur le PC,
avec le compte administrateur de Postgres. dlthub, lui, lira ensuite ces tables
avec le compte en lecture seule dlt_reader (partie E).

Fonctionnement
--------------
- Pour chaque fichier listé dans TABLES, le fichier <table>.csv (ou <table>.csv.gz)
  est lu puis chargé dans datalab.transfermarkt.<table>.
- Rechargement complet : la table est remplacée à chaque lancement
  (le fichier Kaggle est une photo complète des données).
- Écriture rapide avec la commande COPY de Postgres.
- Aucun mot de passe dans le code : il est demandé au lancement (getpass).

Lancement (dans le terminal, venv activé, depuis H:\\projet-aws\\data-lab) :
    python ingestion/transfermarkt/utils/charger_kaggle_postgres.py --dossier H:\\projet-aws\\donnees_kaggle\\transfermarkt
"""

import argparse
import csv
import getpass
import io
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Les 5 fichiers Kaggle retenus pour le projet (décision du 31/10/2026)
TABLES = ["competitions", "clubs", "players", "player_valuations", "transfers"]


def copier_avec_copy(table, conn, keys, data_iter):
    """Insère les lignes avec COPY (bien plus rapide qu'un INSERT ligne par ligne).
    Fonction appelée par pandas.to_sql via le paramètre method=."""
    curseur_brut = conn.connection.cursor()
    tampon = io.StringIO()
    csv.writer(tampon).writerows(data_iter)
    tampon.seek(0)
    colonnes = ", ".join(f'"{k}"' for k in keys)
    nom_table = f'"{table.schema}"."{table.name}"' if table.schema else f'"{table.name}"'
    curseur_brut.copy_expert(f"COPY {nom_table} ({colonnes}) FROM STDIN WITH CSV", tampon)


def trouver_fichier(dossier: Path, table: str) -> Path:
    """Renvoie <table>.csv ou <table>.csv.gz ; erreur claire si absent."""
    for nom in (f"{table}.csv", f"{table}.csv.gz"):
        chemin = dossier / nom
        if chemin.exists():
            return chemin
    raise FileNotFoundError(f"Fichier introuvable pour la table '{table}' dans {dossier}")


def main():
    # Paramètres modifiables au lancement (rien d'écrit en dur dans le traitement)
    p = argparse.ArgumentParser(description="Charge les CSV Kaggle Transfermarkt dans Postgres")
    p.add_argument("--dossier", required=True, help="dossier contenant les fichiers CSV Kaggle")
    p.add_argument("--hote", default="localhost", help="serveur Postgres (défaut : localhost)")
    p.add_argument("--port", type=int, default=5438, help="port Postgres côté PC (défaut : 5438)")
    p.add_argument("--base", default="datalab", help="base cible (défaut : datalab)")
    p.add_argument("--schema", default="transfermarkt", help="schéma cible (défaut : transfermarkt)")
    p.add_argument("--utilisateur", default="admin", help="compte qui écrit (défaut : admin)")
    args = p.parse_args()

    dossier = Path(args.dossier)
    mot_de_passe = getpass.getpass(f"Mot de passe Postgres de '{args.utilisateur}' : ")

    url = URL.create("postgresql+psycopg2", username=args.utilisateur, password=mot_de_passe,
                     host=args.hote, port=args.port, database=args.base)
    moteur = create_engine(url)

    print(f"Cible : {args.hote}:{args.port} / base {args.base} / schéma {args.schema}")
    bilan = []
    for table in TABLES:
        fichier = trouver_fichier(dossier, table)
        df = pd.read_csv(fichier, low_memory=False)          # lecture du CSV
        df.to_sql(table, moteur, schema=args.schema,          # écriture dans Postgres
                  if_exists="replace", index=False,           # replace = rechargement complet
                  method=copier_avec_copy, chunksize=50_000)
        with moteur.connect() as conn:                        # contrôle : lignes en base
            nb = conn.execute(text(f'SELECT COUNT(*) FROM "{args.schema}"."{table}"')).scalar()
        bilan.append((table, len(df), nb, len(df.columns)))
        print(f"✅ {table:<18} fichier : {len(df):>9} lignes | base : {nb:>9} lignes | {len(df.columns)} colonnes")

    erreurs = [t for t, lu, en_base, _ in bilan if lu != en_base]
    if erreurs:
        raise SystemExit(f"❌ Écart de lignes entre fichier et base pour : {erreurs}")
    print("🏁 Chargement terminé : toutes les tables sont complètes.")


if __name__ == "__main__":
    main()
