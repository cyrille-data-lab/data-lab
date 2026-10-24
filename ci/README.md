# ci

Configuration de la **CI/CD AWS** :

- **CodeBuild** : contrôles automatiques lancés à chaque Pull Request.
- **CodePipeline** : déploiement en prod après le merge dans `main`.

Les identifiants des service principals sont stockés dans AWS Secrets Manager, jamais dans ce dossier.

Contenu ajouté à l'étape 6.
