"""
tester_appel_api_football.py
----------------------------
Appel de TEST d'un endpoint API-Football, depuis le PC, avant d'écrire un loader (manuel 6, partie 7, étape 1).
  - fait UNE seule requête (coût : 1 requête du quota) ;
  - affiche le quota restant, les erreurs, le nombre de lignes et la structure d'une ligne ;
  - n'écrit RIEN (ni fichier, ni Databricks).
 
La clé est saisie au clavier (invisible) : elle n'est jamais dans le code, l'historique ni Git.
 
Usage (depuis la racine du dépôt, venv activé) :
    python ingestion/api_football/utils/tester_appel_api_football.py --endpoint /players/topscorers --params league=61,season=2024
"""
import argparse
import json
from getpass import getpass
 
import requests
 
 
def lire_params(texte: str) -> dict:
    """'league=61,season=2024' -> {'league': '61', 'season': '2024'}"""
    return dict(p.split("=", 1) for p in texte.split(",") if p.strip())
 
 
def decrire(objet, prefixe: str = "", niveau: int = 0) -> None:
    """Affiche l'arborescence d'une ligne : clés, type, et taille des listes (= futures tables enfants dlthub)."""
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            chemin = f"{prefixe}__{cle}" if prefixe else cle          # même nommage que dlthub (séparateur __)
            if isinstance(valeur, dict):
                decrire(valeur, chemin, niveau)
            elif isinstance(valeur, list):
                print(f"   📚 {chemin:<45} LISTE de {len(valeur)} élément(s)  -> table enfant dlthub")
                if valeur and isinstance(valeur[0], dict) and niveau < 1:
                    decrire(valeur[0], f"{chemin}[0]", niveau + 1)
            else:
                print(f"   {chemin:<48} {type(valeur).__name__:<6} {str(valeur)[:40]}")
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="Appel de test API-Football (1 requête, aucune écriture)")
    parser.add_argument("--base-url", default="https://v3.football.api-sports.io", help="Adresse de l'API")
    parser.add_argument("--endpoint", default="/players/topscorers", help="Chemin appelé")
    parser.add_argument("--params", default="league=61,season=2024", help="Paramètres : cle=valeur,cle=valeur")
    parser.add_argument("--header", default="x-apisports-key", help="En-tête qui porte la clé")
    args = parser.parse_args()
 
    params = lire_params(args.params)
    cle = getpass("Clé API-Football (saisie invisible) : ").strip()
 
    # --- L'appel (1 requête) ---
    reponse = requests.get(f"{args.base_url}{args.endpoint}", headers={args.header: cle}, params=params, timeout=30)
    del cle                                                           # on ne garde pas la clé en mémoire
    print(f"\nHTTP {reponse.status_code} | {args.endpoint} {params}")
    print(f"Quota restant aujourd'hui (en-tête) : {reponse.headers.get('x-ratelimit-requests-remaining', '?')}")
 
    corps = reponse.json()
 
    # --- Erreurs (API-Football : champ 'errors' non vide) ---
    if corps.get("errors"):
        print("❌ Erreur API :", corps["errors"])
        return
 
    # --- Où sont les lignes ? ---
    print("Clés de l'enveloppe :", list(corps.keys()))
    lignes = corps.get("response", [])
    print(f"Nombre de lignes dans 'response' : {len(lignes)}")
    if not lignes:
        return
 
    # --- Structure d'une ligne (aplatie comme le fera dlthub) ---
    print("\n=== Structure de la 1re ligne ===")
    decrire(lignes[0])
 
    # --- Taille des listes sur toutes les lignes (combien de lignes enfants par joueur ?) ---
    tailles = [len(l.get("statistics", [])) for l in lignes if isinstance(l, dict)]
    if tailles:
        print(f"\n'statistics' : de {min(tailles)} à {max(tailles)} élément(s) par ligne")
 
    # --- Aperçu lisible : 3 premières lignes, nom + buts ---
    print("\n=== Aperçu ===")
    for l in lignes[:3]:
        stat = (l.get("statistics") or [{}])[0]
        print(f"   {l['player']['name']:<25} {stat.get('team', {}).get('name', ''):<20} "
              f"buts={stat.get('goals', {}).get('total')}  compétition={stat.get('league', {}).get('name')}")
 
 
if __name__ == "__main__":
    main()