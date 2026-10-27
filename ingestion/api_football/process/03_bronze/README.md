# 03_bronze

Lecture des fichiers de la landing et écriture en tables Delta dans le schéma `bronze`
(tables préfixées `api_football_`, avec colonnes techniques de chargement).

- `01_loaders` : un notebook par table bronze.
- `02_orchestration` : notebook qui lance les loaders dans l'ordre.