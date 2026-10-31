"""
Test de connexion à Databricks en tant que service principal (OAuth M2M).

But : vérifier, AVANT de lancer dlthub, que le service principal décrit dans
.dlt/secrets.toml peut :
  1. s'authentifier (client_id + client_secret) ;
  2. utiliser le SQL warehouse (http_path) ;
  3. voir le catalog, le schéma bronze et le volume de transit de dlthub.

Les valeurs sont lues dans .dlt/secrets.toml (fichier local, ignoré par Git) :
rien n'est écrit dans ce script.

Lancement (venv activé, depuis H:\\projet-aws\\data-lab) :
    python ingestion/transfermarkt/utils/tester_connexion_databricks.py
"""

import tomllib
from pathlib import Path

from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal

FICHIER_SECRETS = Path(".dlt/secrets.toml")   # chemin relatif : lancer depuis la racine du dépôt


def main():
    # 1. Lecture des paramètres de connexion dans le fichier de secrets local
    with FICHIER_SECRETS.open("rb") as f:
        cred = tomllib.load(f)["destination"]["databricks"]["credentials"]

    hote, chemin_http, catalog = cred["server_hostname"], cred["http_path"], cred["catalog"]

    # 2. Fournisseur d'identité OAuth « machine à machine » : le service principal
    def fournisseur_identite():
        config = Config(host=f"https://{hote}",
                        client_id=cred["client_id"],
                        client_secret=cred["client_secret"])
        return oauth_service_principal(config)

    # 3. Connexion au SQL warehouse et requêtes de contrôle
    with sql.connect(server_hostname=hote, http_path=chemin_http,
                     credentials_provider=fournisseur_identite) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT current_user()")
            print("✅ Connecté en tant que :", curseur.fetchone()[0])

            curseur.execute(f"SHOW SCHEMAS IN `{catalog}`")
            print(f"✅ Schémas visibles dans {catalog} :", sorted(r[0] for r in curseur.fetchall()))

            curseur.execute(f"SHOW VOLUMES IN `{catalog}`.`landing`")
            print(f"✅ Volumes de {catalog}.landing :", sorted(r[1] for r in curseur.fetchall()))

    print("🏁 Test réussi : le service principal peut utiliser le warehouse et le catalog.")


if __name__ == "__main__":
    main()
