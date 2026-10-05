# Comprendre et adapter les workflows GitHub Actions

## Fonctionnement fourni

Le dépôt contient deux workflows actifs après leur dépôt dans GitHub. Ils utilisent des machines temporaires `ubuntu-latest`, et non un runner installé sur votre ordinateur. Aucun secret OpenProject ni URL Ollama n'est nécessaire dans GitHub Actions.

`tests.yml` vérifie le robot sur les mises à jour de `main` et sur les Pull Requests. Il installe le projet, exécute la suite unittest puis lance la simulation des sept agents.

`evidence.yml` se déclenche à l'ouverture, à la réouverture et à la mise à jour d'une PR. Il prépare les outils depuis le commit de la branche cible, puis analyse le SHA de tête de la PR. Il n'utilise pas le commit de fusion synthétique comme identifiant des preuves.

## Les étapes de collecte

1. `trusted/` reçoit la version du robot présente sur la branche cible, donc celle à examiner et approuver avant de l'utiliser.
2. `target/` reçoit le commit exact de la PR, avec `persist-credentials: false`.
3. Le Dockerfile de `trusted/` installe les outils dans une image de runner.
4. Le conteneur copie `target/` dans son espace temporaire. Son réseau est désactivé, les capacités Linux sont retirées et les ressources sont bornées.
5. Le collecteur exécute Ruff, Bandit, Gitleaks et pytest. Les tests n'ont accès ni au jeton OpenProject ni à celui du robot GitHub.
6. `review.ci normalize` vérifie le type du fichier, sa taille, son schéma et son SHA. Seul le JSON normalisé est placé dans `artifacts/`.
7. L'artefact `review-evidence-SHA` est conservé sept jours.
8. `review.ci gate` termine le job en échec si un contrôle manque, présente des écarts, ou si la couverture ne satisfait pas le seuil.

L'artefact est enregistré avant l'application du seuil pour qu'une revue puisse expliquer un échec. Un échec de construction du runner ou un JSON invalide ne produit pas d'artefact exploitable.

## Configurer les chemins de votre application

Dans les variables Actions du dépôt, deux valeurs contrôlent le périmètre :

| Variable | Valeur initiale | À adapter |
|---|---|---|
| `REVIEW_SCAN_PATH` | `example_app` | Dossier relatif contenant le code à analyser avec Ruff et Bandit |
| `REVIEW_COVERAGE_SOURCE` | `example_app` | Module ou dossier dont la couverture doit être mesurée |

Par exemple, pour une application placée dans `src`, utilisez `src` pour ces deux variables si cela correspond à votre organisation Python. Le collecteur refuse un dossier d'analyse situé hors du dépôt. pytest découvre les tests depuis la racine du dépôt. Gitleaks parcourt l'arbre de travail entier ; il ne remplace pas un scan de tout l'historique Git.

Les règles Ruff initiales sont `E4,E7,E9,F`. Le seuil de couverture est 80 %. La politique du contrôle CI est dans `review/ci.py`, et celle de la recommandation des agents dans `review/agents/agent7_synthesis.py`. Si vous changez la politique, gardez ces deux endroits cohérents et testez les conséquences.

Le runner contient les outils du robot. Pour une vraie application, ajoutez ses dépendances examinées à `Dockerfile.runner`. L'installation se fait au moment de construire l'image, avant l'exécution sans réseau. Ne lancez pas à cette étape privilégiée un script d'installation fourni par la PR.

## Exemple avec un dépôt applicatif existant

Le parcours recommandé pour débuter place le robot à la racine du dépôt fourni. Pour un dépôt existant, n'écrasez pas son `pyproject.toml` ou son dossier `tests`.

Une solution consiste à placer le robot dans `tools/revue-ia-github/`, à l'exclusion de ses dossiers `.git`, `.venv`, `.env`, `runs` et de ses propres workflows. Adaptez le workflow de collecte dans le dépôt applicatif :

```bash
python -m pip install ./trusted/tools/revue-ia-github
docker build \
  -f trusted/tools/revue-ia-github/Dockerfile.runner \
  -t revue-ia-runner:local trusted/tools/revue-ia-github
```

Les chemins `target`, `runner-output` et `artifacts` du workflow restent relatifs à l'espace de travail Actions. Le programme `review.ci` vient du paquet installé depuis la version approuvée. Vérifiez les imports Python et les dépendances propres à votre application dans le runner. Le workflow `tests.yml` du robot doit alors être adapté ou remplacé par vos contrôles habituels.

Autre possibilité : conserver le robot dans un dépôt distinct, le récupérer dans `trusted/` avec un `repository` explicite et un `ref` fixé à un commit approuvé. Cela exige de vérifier les droits de lecture de ce dépôt. Le `GITHUB_TOKEN` d'un dépôt n'accorde pas automatiquement l'accès à un autre dépôt privé. Ce raccordement n'est pas configuré sans connaître vos dépôts.

## Reproduire la collecte dans un conteneur local

Après avoir construit l'image avec `docker build -f Dockerfile.runner -t revue-ia-runner:local .`, remplacez les chemins absolus :

```bash
mkdir -p /CHEMIN/evidence-sortie
docker run --rm --network=none --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --pids-limit=256 --memory=4g --cpus=2 \
  --tmpfs /tmp:rw,nosuid,size=2g \
  --mount type=bind,src=/CHEMIN/clone-propre,dst=/source,readonly \
  --mount type=bind,src=/CHEMIN/evidence-sortie,dst=/out \
  revue-ia-runner:local sh -c \
  'cp -R /source /tmp/repo && python scripts/collect_evidence.py --repo /tmp/repo --out /out/evidence.json --run-tests --scan-path example_app --coverage-source example_app'
```

Utilisez un clone ne contenant que le code nécessaire, et un dossier de sortie vide. Ne montez ni votre répertoire personnel, ni un jeton, ni le socket Docker dans ce conteneur. Des tests d'intégration nécessitant une base de données demandent un environnement de test supplémentaire.

## Récupération et revue locale

Téléchargez l'artefact de la bonne exécution depuis GitHub Actions, décompressez-le puis lancez :

```bash
python -m review.cli review \
  --ticket 42 --repo VOTRE_COMPTE/VOTRE_DEPOT --pr 1 \
  --evidence /CHEMIN/evidence.json --standards examples/STANDARDS.md
```

Les preuves d'un ancien commit sont refusées. Un fichier JSON valide n'est pas une preuve d'authenticité : le code testé peut tenter de falsifier ses propres résultats. Vérifiez la provenance du workflow, le commit et la pertinence des tests lors de la revue humaine. Les artefacts restent des données ; ils ne doivent jamais être exécutés sur la machine qui détient les jetons.

## Permissions et exploitation

Les workflows utilisent `contents: read` et ne transmettent aucun secret personnalisé au code de la PR. N'ajoutez pas de jeton OpenProject à ces jobs. Évitez de les convertir en `pull_request_target` avec checkout et exécution de la branche de PR. Un tel mélange change la frontière de confiance.

Pour un dépôt public, les contributions externes peuvent nécessiter l'approbation d'un mainteneur avant l'exécution de leurs workflows. Les workflows sont eux-mêmes des fichiers à faire examiner : un contributeur peut proposer leur modification. Protégez la branche cible et la politique des contrôles selon les fonctions disponibles dans votre offre.

Les actions sont référencées par des tags de version pour le prototype. Après recette, figez leurs SHA, les versions des dépendances et les digests des images. Les workflows fournis n'ont pas été exécutés dans votre compte lors de la préparation du dossier.

## Sources officielles

- [Événements et comportement des Pull Requests](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
- [Authentification GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).
- [Action checkout](https://github.com/actions/checkout).
- [Action setup-python](https://github.com/actions/setup-python).
- [Action upload-artifact](https://github.com/actions/upload-artifact).
