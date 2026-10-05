# Changements de la version GitHub

La version 0.2.0 remplace la forge locale du premier prototype par GitHub.com. OpenProject et les sept agents sont conservés.

- Le connecteur utilise les chemins `/repos/PROPRIETAIRE/DEPOT/...`, l'authentification Bearer et une version d'API explicite.
- Le diff est demandé au même endpoint que la PR avec le type de contenu `application/vnd.github.diff`.
- Les commentaires sont publiés via l'API des commentaires d'issues, également utilisée pour les PR.
- La configuration locale utilise `GITHUB_API_URL`, `GITHUB_API_VERSION` et `GITHUB_TOKEN`.
- Le Compose ne démarre plus de forge Git. Il conserve OpenProject et Ollama en option.
- Deux workflows et un modèle de PR sont fournis dans `.github/`.
- Un validateur borne et vérifie les artefacts de preuves avant leur import.
- Le périmètre Ruff et Bandit peut cibler le dossier applicatif avec `--scan-path`.
- Une petite application de division et ses tests permettent un premier essai.
- Le rapport utilise le schéma 2 et indique `forge: github`. Les rapports de l'ancienne version sont refusés.
- Le guide, le schéma d'architecture et les exemples sont réécrits pour GitHub.

Les fichiers de la version précédente restent dans leur dossier initial. Utilisez le nouveau dossier `revue-ia-github` et recréez son `.env` avec les variables GitHub. Aucun transfert vers votre compte GitHub n'a été réalisé.
