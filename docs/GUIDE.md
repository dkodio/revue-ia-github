# Revue de code avec GitHub OpenProject et sept agents IA

## 1 La version GitHub du projet

Cette version utilise **GitHub pour le code et les Pull Requests**, **OpenProject Community Edition pour les tickets** et **Ollama pour le modèle local**. Les sept agents Python sont conservés. Un connecteur GitHub remplace le connecteur de la première version, et deux workflows GitHub Actions sont inclus.

GitHub héberge votre dépôt et les contrôles automatisés. OpenProject et le modèle peuvent rester sur votre machine ou votre serveur privé. Vous n'avez pas besoin d'installer une forge Git locale. Le socle Python est fourni sous licence MIT ; GitHub est un service distinct et la solution ne doit donc pas être présentée comme entièrement open source.

La première version cible une application Python. Un petit module `example_app/calculator.py` et ses trois tests sont fournis pour essayer le parcours. Les sept agents peuvent analyser d'autres langages, mais les outils de contrôle doivent alors être adaptés.

**Livrable : version 0.2.0.** Le code et la simulation ont été vérifiés localement. Aucun dépôt GitHub n'a été créé ni aucun commentaire envoyé dans votre compte pendant cette préparation. L'exécution réelle des workflows et des services doit être validée après votre installation. Les détails sont dans `docs/VALIDATION.md`.

## 2 Les outils retenus à chaque étape

| Étape | Outil | Résultat |
|---|---|---|
| Décrire le besoin | OpenProject Community Edition | Ticket et critères d'acceptation |
| Développer et versionner | Votre éditeur, Git et GitHub | Branche et commits |
| Demander une revue | Pull Request GitHub | Diff, discussion et lien du ticket |
| Vérifier le robot | GitHub Actions et unittest | Tests du programme de revue |
| Contrôler le code de la PR | GitHub Actions et conteneur jetable | Ruff, Bandit, Gitleaks, pytest et couverture |
| Transmettre les preuves | Artefact GitHub Actions | Fichier `evidence.json` lié au commit |
| Coordonner la revue IA | Orchestrateur Python fourni | Agents 1 à 7 |
| Exécuter le modèle | Ollama et Qwen2.5-Coder 7B | Analyse locale et sorties JSON |
| Restituer | Markdown, JSON et API GitHub | Rapport local et commentaire général de PR |
| Mettre à jour le suivi | API OpenProject | Commentaire de synthèse dans le ticket |
| Décider de la fusion | Réviseur humain dans GitHub | Approbation et fusion |
| Clôturer le besoin | OpenProject | Clôture manuelle après fusion |
| Suivre les revues | SQLite et Streamlit | Historique et tableau de bord local |

GitHub Actions permet de déclencher un workflow à l'ouverture ou à la mise à jour d'une PR. Les fichiers fournis utilisent l'événement `pull_request`. [Documentation des événements](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

Le modèle proposé est Qwen2.5-Coder-7B-Instruct, publié sous Apache 2.0. Ce choix sert à démarrer ; évaluez sa précision sur votre application. OpenProject Community Edition est auto-hébergeable et open source. [Fiche du modèle](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct), [OpenProject Community](https://www.openproject.org/fr/edition-community/).

## 3 Comprendre la nouvelle architecture

```text
OpenProject : ticket et exigences ─────────────┐
                                              │
GitHub : branche puis Pull Request ────────────┤
         │                                    ▼
         └─ GitHub Actions              Orchestrateur Python local
            │                                │
            ├─ Tests du robot                 ├─ Agent 1 Exigences
            └─ Ruff, Bandit, Gitleaks,         ├─ Agent 2 Analyse du code
               pytest et couverture          ├─ Agent 3 Qualité
                     │                       ├─ Agent 4 Conformité
               evidence.json ───────────────► ├─ Agent 5 Tests
                                             ├─ Agent 6 Sécurité
Ollama local ◄───────────────────────────────► └─ Agent 7 Synthèse
                                                      │
                                 Rapport et recommandation
                                                      │
                          Commentaires GitHub et OpenProject
                                                      │
                               Approbation humaine et fusion
```

**Deux endroits exécutent le travail.** GitHub Actions exécute les contrôles sur une machine temporaire fournie par GitHub. Le robot IA tourne sur votre machine, où il peut joindre OpenProject et Ollama. Une adresse `localhost` utilisée dans GitHub Actions désignerait la machine GitHub, pas votre ordinateur.

Les workflows inclus ne reçoivent donc aucun jeton OpenProject et n'appellent pas votre Ollama local. Après un contrôle, vous téléchargez le fichier de preuves et vous le transmettez au robot. La commande `review.watch` automatise les nouvelles analyses de PR ; le transfert des artefacts GitHub vers votre machine reste manuel dans cette version.

Les sept agents utilisent le même modèle et s'exécutent successivement. Il n'est pas nécessaire de charger sept modèles. Les tickets, les commentaires et le code sont des données à examiner, jamais des instructions de modification ou d'exécution pour les agents.

## 4 Préparer les comptes et la machine

Il vous faut un compte GitHub, Git, Python 3.11 ou 3.12, un moteur Docker compatible Compose pour OpenProject et, pour le mode réel, Ollama. La démonstration du robot n'exige ni compte GitHub, ni Docker, ni modèle.

Les commandes ci-dessous ciblent macOS ou Linux. Sous Windows, vous pouvez utiliser un environnement Linux WSL2 configuré pour vos conteneurs. Sur macOS, Colima avec Docker CLI et Compose est une option open source. Ollama installé directement sur macOS est préférable au conteneur pour profiter de l'accélération disponible sur Apple Silicon. [Colima](https://github.com/abiosoft/colima), [Ollama](https://ollama.com/).

```bash
python3 --version
git --version
docker version
docker compose version
```

Pour un essai avec tous les services locaux, prévoyez plutôt 24 à 32 Go de mémoire pour du confort ; 16 Go peut convenir à des essais plus modestes. Ce sont des estimations à mesurer, pas des minima garantis. La taille du diff et du contexte du modèle influence fortement la consommation. Gardez plusieurs dizaines de Go de disque disponibles.

GitHub Actions et l'hébergement GitHub dépendent de votre offre et de vos quotas. Vérifiez ceux de votre compte avant de multiplier les exécutions. Cette adaptation ne suppose aucun abonnement particulier.

## 5 Installation et premier parcours en quatorze étapes

### Étape 1 Décompresser et lancer le robot en simulation

Décompressez `Projet-revue-IA-GitHub.zip`, puis ouvrez un terminal dans le dossier `revue-ia-github` :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m review.cli demo
```

La commande affiche un dossier `runs/IDENTIFIANT`. Il contient `report.md` et `review.json`. Le rapport doit afficher les sept agents et la mention de simulation. Aucun service n'est contacté et aucune publication n'est effectuée. Ce test valide le fonctionnement du programme, pas la qualité d'une analyse IA.

### Étape 2 Créer votre dépôt GitHub

Dans GitHub, créez un dépôt vide nommé, par exemple, `revue-ia-github`. Choisissez sa visibilité selon la confidentialité de votre code. Ne lui ajoutez pas un README ou une licence depuis l'assistant : le dossier fourni les contient déjà.

Dans le dossier du projet, remplacez `VOTRE_COMPTE` par votre utilisateur ou organisation :

```bash
git init -b main
git add .
git commit -m "Initialiser la revue IA avec GitHub et OpenProject"
git remote add origin https://github.com/VOTRE_COMPTE/revue-ia-github.git
git push -u origin main
```

Utilisez votre authentification habituelle de développeur pour pousser : gestionnaire d'identifiants, GitHub CLI ou clé SSH. Le jeton limité du robot, créé plus loin, n'a pas vocation à pousser du code. Vérifiez dans GitHub la présence de `.github/workflows/tests.yml` et `.github/workflows/evidence.yml` sur `main` avant d'ouvrir la première PR.

Le dépôt initial peut contenir le robot et l'application d'exemple. Si votre vraie application possède déjà un dépôt, l'étape 14 explique comment la raccorder sans remplacer vos fichiers.

### Étape 3 Préparer les variables locales

```bash
python scripts/init_env.py
```

Cette commande crée `.env` et une clé aléatoire pour OpenProject sans écraser un fichier existant. Le fichier est exclu par `.gitignore`. Les jetons et les services utilisés par le robot sont configurés dans ce fichier, sur votre machine uniquement.

La configuration GitHub est :

```dotenv
GITHUB_API_URL=https://api.github.com
GITHUB_API_VERSION=2026-03-10
GITHUB_TOKEN=VOTRE_JETON_GITHUB
```

L'URL de l'API est `https://api.github.com`, et non l'adresse de votre page de dépôt. Le projet est préparé pour GitHub.com ; une instance GitHub Enterprise nécessiterait une validation supplémentaire de son URL et de sa version d'API.

### Étape 4 Démarrer OpenProject

```bash
docker compose up -d openproject
docker compose ps
docker compose logs --tail=100 openproject
```

Ouvrez `http://localhost:8080`. Attendez la fin de l'initialisation. Le compte initial documenté pour ce conteneur est `admin`, mot de passe `admin` ; changez-le immédiatement, puis créez votre projet. Les données sont conservées dans des volumes.

Le Compose contient seulement OpenProject et un profil Ollama facultatif. GitHub est utilisé comme service distant. L'image OpenProject tout-en-un sert au laboratoire ; suivez l'installation officielle séparant les composants pour la production. [Démarrage OpenProject](https://www.openproject.org/docs/installation-and-operations/installation/docker/), [installation Compose](https://www.openproject.org/docs/installation-and-operations/installation/docker-compose/).

### Étape 5 Installer Ollama et le modèle

Installez Ollama depuis son site officiel puis exécutez :

```bash
ollama pull qwen2.5-coder:7b
ollama list
```

Si l'application n'a pas déjà lancé le serveur, utilisez `ollama serve` dans un autre terminal. Gardez `OLLAMA_URL=http://localhost:11434` dans `.env`.

Alternative en conteneur, à utiliser à la place du serveur natif sur ce même port :

```bash
docker compose --profile llm-container up -d ollama
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

Cette alternative n'active pas automatiquement un GPU. Le client demande une réponse JSON conforme à un schéma et Pydantic valide sa structure. [Sorties structurées Ollama](https://docs.ollama.com/capabilities/structured-outputs).

### Étape 6 Créer les accès du robot

Dans GitHub, ouvrez vos paramètres, puis **Developer settings → Personal access tokens → Fine-grained tokens**. Créez un jeton avec une expiration, choisissez le propriétaire concerné et limitez-le au dépôt du pilote.

Pour les fonctions du robot, accordez **Pull requests : Read and write** afin de lire la PR et publier son commentaire. Metadata reste l'accès de base de GitHub. Le robot fourni ne clone pas le dépôt et ne pousse aucun commit : il lit le diff par l'API. Une organisation peut imposer une approbation du jeton ou des règles d'accès supplémentaires.

Le même endpoint de commentaire peut être utilisé avec la permission Pull requests en écriture ; il n'est pas nécessaire de donner tous les droits d'administration. [API des Pull Requests](https://docs.github.com/en/rest/pulls/pulls), [API des commentaires](https://docs.github.com/en/rest/issues/comments).

Collez le jeton dans `GITHUB_TOKEN` du `.env` local. Ne le mettez pas dans le code, le fichier YAML ou une PR. Les workflows fournis utilisent leur propre `GITHUB_TOKEN` automatique, limité à `contents: read` ; ils n'ont pas besoin de votre jeton personnel. [Authentification des workflows](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).

Dans OpenProject, créez un utilisateur de service autorisé à lire les tickets du projet et à ajouter des commentaires. Générez son jeton API puis renseignez `OPENPROJECT_TOKEN`. Le connecteur utilise Basic Auth avec le nom fixe `apikey` et le jeton comme mot de passe. [Authentification OpenProject](https://www.openproject.org/docs/api/introduction/).

### Étape 7 Créer le ticket et la Pull Request

Créez un ticket OpenProject à partir de `examples/TICKET.md` et notez son numéro réel, par exemple 42. Le ticket décrit la fonction `divide` et trois critères : division normale, diviseur nul et valeur négative.

Sur votre dépôt local :

```bash
git switch -c feature/op-42-division
```

Modifiez `example_app/calculator.py` ou ajoutez un cas de test dans `tests/test_calculator.py`. Enregistrez puis poussez vos changements :

```bash
git add example_app tests
git commit -m "OP-42 compléter les cas de division"
git push -u origin feature/op-42-division
git rev-parse HEAD
```

Ouvrez une Pull Request vers `main` dans GitHub. Le modèle de description fourni vous demande le ticket, ses critères et les vérifications. L'identifiant OpenProject n'est pas automatiquement déduit du titre : vous le transmettrez explicitement au robot.

### Étape 8 Laisser GitHub Actions contrôler la PR

Ouvrez l'onglet **Actions** ou la section des contrôles de votre PR. Deux workflows sont fournis :

| Workflow | Fonction |
|---|---|
| Tests du robot | Teste le code du robot et sa démonstration |
| Preuves de la Pull Request | Exécute les analyseurs et produit le fichier de preuves |

Le second workflow récupère le collecteur depuis le commit de la branche cible, puis récupère le SHA exact de la PR dans un dossier séparé. Il construit l'image de contrôle, copie le code dans un conteneur temporaire sans réseau et y lance les outils. Aucun jeton OpenProject ou Ollama n'est transmis au code testé.

Par défaut, Ruff et Bandit analysent `example_app`, et la couverture porte sur `example_app`. pytest découvre les tests du dépôt. Gitleaks inspecte l'arbre de travail entier. Ce réglage sert à vérifier l'application de démonstration ; il ne prétend pas auditer le robot complet avec les analyseurs statiques.

Pour votre application, configurez dans **Settings → Secrets and variables → Actions → Variables** les variables `REVIEW_SCAN_PATH` et `REVIEW_COVERAGE_SOURCE`, par exemple `src`. Installez aussi les dépendances applicatives nécessaires dans `Dockerfile.runner`, depuis une liste examinée et intégrée à `main` avant la PR concernée. Ne remplacez pas les outils approuvés par un script provenant de la PR.

L'analyse Ruff utilise `E4,E7,E9,F`, soit des contrôles de base. Les conventions de mise en forme supplémentaires peuvent être ajoutées dans le collecteur de confiance. Les seuils sont pédagogiques : tout contrôle absent ou avec constats échoue, et la couverture minimale est de 80 %.

### Étape 9 Télécharger les preuves du bon commit

Dans l'exécution du workflow **Preuves de la Pull Request**, téléchargez l'artefact nommé `review-evidence-SHA`. Décompressez-le dans un dossier local distinct du dépôt analysé, par exemple `evidence/`. Il contient `evidence.json`.

Vérifiez que l'exécution correspond à votre dépôt, à la bonne PR et à son dernier commit. Les preuves sont enregistrées avant l'étape qui applique les seuils : un workflow en échec à cause d'un défaut peut donc fournir un artefact utile. Un échec de construction ou d'installation peut en revanche empêcher sa création.

Le fichier est validé comme JSON, borné en taille et lié à un SHA. Ce n'est pas une attestation cryptographique et cela ne prouve pas l'honnêteté de tests écrits par un contributeur. Le téléchargement et le placement du fichier sont manuels dans cette version. Les artefacts sont conservés sept jours par le workflow fourni.

Vous pouvez aussi collecter localement dans un environnement jetable, sans jeton, après avoir installé les outils de `requirements-tools.txt` et Gitleaks :

```bash
python /CHEMIN/revue-ia-github/scripts/collect_evidence.py \
  --repo /CHEMIN/clone-propre \
  --out /CHEMIN/evidence.json \
  --run-tests --scan-path example_app --coverage-source example_app
```

Le dépôt doit être propre. `--run-tests` autorise l'exécution du code de tests ; sans ce paramètre, le contrôle reste `not_run`. Pour du code de PR, utilisez le conteneur isolé décrit dans `docs/GITHUB_ACTIONS.md` plutôt que votre environnement de travail contenant des secrets.

### Étape 10 Lancer les sept agents sur la PR GitHub

Sur la machine où OpenProject et Ollama sont accessibles, dans le dossier du robot :

```bash
source .venv/bin/activate
python -m review.cli review \
  --ticket 42 \
  --repo VOTRE_COMPTE/revue-ia-github \
  --pr 1 \
  --evidence /CHEMIN/evidence.json \
  --standards examples/STANDARDS.md
```

Remplacez le numéro de ticket, le dépôt, le numéro de PR et le chemin par vos valeurs. Le programme refuse des preuves associées à un autre commit. Sans `--evidence`, il effectue la lecture IA du diff mais signale les contrôles manquants.

Le programme lit le ticket, vérifie la stabilité des commits source et cible pendant la lecture du diff, puis appelle les sept agents. Les réponses invalides sont retentées une fois. Une analyse en échec apparaît `incomplete` et la commande termine avec le code 2 après sauvegarde du rapport. Les diffs de plus de 45 000 caractères sont refusés : découpez la PR plutôt que d'ignorer silencieusement une partie du code.

### Étape 11 Lire et publier le rapport

Ouvrez `runs/IDENTIFIANT/report.md`. Confirmez le SHA analysé, les preuves, les critères inconnus et les observations importantes. La source `llm` indique une observation du modèle ; `tool` indique un résultat ajouté à partir d'un analyseur.

| Recommandation | Sens |
|---|---|
| `corrections_recommandees` | Des écarts ou des risques sont à examiner et à corriger |
| `revue_humaine_requise` | Le périmètre ou les preuves restent limités |
| `pret_pour_validation_humaine` | Les contrôles disponibles satisfont les règles, avec approbation humaine encore obligatoire |

Le mode réel rappelle systématiquement qu'il analyse le diff. Une analyse sans défaut détecté reste donc normalement `revue_humaine_requise`. La couverture de lignes ne prouve pas la conformité du comportement métier.

Après lecture, publiez explicitement le résumé :

```bash
python -m review.cli publish runs/IDENTIFIANT/review.json
```

La commande ajoute un commentaire général dans la PR GitHub et dans le ticket OpenProject. Elle ne fusionne pas la PR et ne change pas le statut du ticket. Les annotations ligne par ligne et le téléversement automatique du rapport complet ne sont pas implémentés.

Le programme vérifie que la PR et le ticket n'ont pas changé depuis l'analyse. Ce n'est pas un verrou transactionnel distant : le réviseur doit encore confirmer le bon commit au moment de fusionner. Le journal `publication.json` distingue `github` et `openproject`. Si une destination reste `sending`, vérifiez si son commentaire existe avant de reprendre. Marquez-la `sent` s'il existe ; supprimez seulement cette entrée si son absence est confirmée. Utilisez un seul processus de publication par rapport.

Les anciens rapports de la première version ne sont pas acceptés : les rapports GitHub utilisent le schéma 2. Refaire la revue empêche de publier par erreur une ancienne analyse sur une autre plateforme.

### Étape 12 Corriger et approuver dans GitHub

Après une correction, poussez un nouveau commit. GitHub Actions relance les contrôles. Téléchargez les nouvelles preuves et relancez les agents sur ce commit. Le réviseur examine le rapport et les tests, puis approuve la PR dans GitHub.

Dans les réglages du dépôt, configurez une protection de `main` ou un ruleset selon les fonctions disponibles dans votre offre. Exigez une approbation humaine et les contrôles pertinents, notamment `unit-tests` et `collect-evidence`, une fois qu'ils ont été exécutés. Faites protéger les workflows et le code du robot par une revue de personnes de confiance.

Une personne fusionne la bonne version, puis clôture le ticket OpenProject. L'agent ne possède aucune fonction de fusion automatique. [Protection des branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

### Étape 13 Activer la surveillance et le tableau de bord

Pour surveiller une PR précise depuis votre machine :

```bash
python -m review.watch \
  --ticket 42 --repo VOTRE_COMPTE/revue-ia-github --pr 1 \
  --evidence /CHEMIN/evidence.json \
  --standards examples/STANDARDS.md --interval 60
```

Le processus détecte les changements par interrogation des API. Laissez-le tourner et utilisez `Ctrl+C` pour l'arrêter. Les preuves d'un ancien commit sont exclues. Quand vous remplacez le fichier local par les nouvelles preuves téléchargées, une nouvelle analyse est déclenchée.

Ajoutez `--publish` si vous souhaitez autoriser la publication automatique des synthèses après les analyses terminées. Il ne s'agit toujours pas d'une approbation de PR. Une publication échouée doit être réconciliée manuellement avec son journal. Le mode `--once` réalise un seul cycle.

Pour afficher l'historique :

```bash
python -m pip install -r requirements-dashboard.txt
streamlit run dashboard.py --server.address 127.0.0.1
```

Le tableau lit `runs/history.sqlite3` et masque les simulations par défaut. Pour exporter :

```bash
python -m review.cli export --out historique.csv
```

### Étape 14 Raccorder votre véritable application

Commencez par valider le petit exemple. Pour un nouveau projet, vous pouvez ensuite ajouter votre application au même dépôt et ajuster les chemins d'analyse ainsi que les dépendances du runner.

Si votre application possède déjà son dépôt, vous pouvez garder le robot dans un dépôt séparé et l'utiliser immédiatement en local avec `--repo ORGANISATION/APPLICATION`. Le connecteur n'exige pas que les fichiers du robot soient présents dans la PR analysée.

Les workflows livrés supposent en revanche que le robot, son Dockerfile et ses scripts sont à la racine de la branche cible du dépôt analysé. Ne les copiez pas tels quels dans un dépôt existant dont la structure diffère. Intégrez les fichiers du robot dans un dossier dédié puis adaptez les chemins, ou utilisez un dépôt de robot distinct avec un checkout sur une version explicitement approuvée. Les étapes à modifier sont détaillées dans `docs/GITHUB_ACTIONS.md`.

Pour changer de langage, adaptez le collecteur et les commandes de test : les agents seuls ne remplacent pas les analyseurs du langage. Le fichier de preuves doit garder le même contrat JSON et le SHA exact de la PR.

## 6 Comprendre le code des sept agents

Le code complet est dans `review/agents/`. La version HTML du guide affiche aussi chaque fichier dans une section dépliable. Les agents partagent les contrats de `review/models.py`, le client de `review/llm.py` et les fonctions de `review/agents/common.py`.

| Agent et fichier | Entrées | Résultat attendu |
|---|---|---|
| 1 `agent1_requirements.py` | Sujet et description du ticket | Critères identifiés, contraintes et ambiguïtés |
| 2 `agent2_code.py` | Diff et standards | Risques techniques avec preuves et corrections proposées |
| 3 `agent3_quality.py` | Diff et rapport Ruff | Lisibilité et écarts de qualité |
| 4 `agent4_compliance.py` | Critères de l'agent 1 et diff | Matrice des critères étayés, non satisfaits ou inconnus |
| 5 `agent5_tests.py` | Critères, diff et preuves de tests | Limites de test et cas supplémentaires à écrire |
| 6 `agent6_security.py` | Diff, Bandit et Gitleaks | Risques de sécurité et emplacements à examiner |
| 7 `agent7_synthesis.py` | Six résultats précédents | Synthèse rédactionnelle et recommandation calculée |

### Agent 1 Analyse du ticket OpenProject

La fonction `run(context, model)` envoie le texte du ticket au modèle. Elle demande des critères numérotés `CA-1`, `CA-2`, etc. La preuve doit correspondre au besoin écrit. Un besoin absent n'est pas inventé. Le rôle ne vérifie pas encore si le code satisfait le critère.

### Agent 2 Analyse technique du code

Cet agent cherche les erreurs logiques, les cas limites et les incompatibilités visibles dans le diff. Un constat utile nomme le fichier, décrit la conséquence et explique la correction. Le modèle ne dispose pas du dépôt complet ; il doit signaler cette limite.

### Agent 3 Qualité du code

Le modèle commente la lisibilité et la maintenabilité. Les constats Ruff sont ensuite ajoutés directement par le programme. Cela évite qu'un résumé positif du modèle fasse disparaître une erreur réellement détectée par l'analyseur.

### Agent 4 Conformité fonctionnelle

Il compare les exigences au code. `supported` signifie « étayé par le code visible », pas « comportement prouvé par un test ». Si le modèle oublie un critère, le programme le réintroduit avec l'état `unknown`. Il s'agit de conformité aux exigences du ticket, pas de conformité juridique ou réglementaire.

### Agent 5 Tests

Il distingue les tests réellement exécutés des tests proposés. La couverture provient de pytest-cov ; une valeur absente reste inconnue. Cet agent ne lance pas pytest lui-même et n'exécute jamais les exemples de code suggérés par le modèle.

### Agent 6 Sécurité

Bandit analyse les risques propres au code Python. Gitleaks recherche des secrets potentiels. Le modèle ajoute une lecture contextuelle du diff, notamment sur les validations d'entrée et les permissions. Les résultats des outils restent présents dans le rapport. Un secret détecté doit être révoqué ou remplacé selon votre procédure ; supprimer sa ligne ne suffit pas à annuler sa divulgation.

### Agent 7 Synthèse et recommandation

Le modèle rédige la synthèse. La fonction `recommendation` calcule séparément la recommandation à partir des erreurs, des preuves manquantes, des critères et du seuil de couverture. Le modèle ne peut pas effacer un échec de contrôle avec une phrase rassurante. Aucun résultat ne déclenche une fusion automatique.

### Contrats des données

Un constat contient `severity`, `title`, `evidence`, `recommendation`, `file`, `line` et `source`. La source `llm` identifie une observation du modèle ; `tool` identifie un constat ajouté par le programme à partir d'un outil. Le client Ollama force ses propres constats à `llm`.

Chaque résultat d'agent contient son numéro, son état, sa synthèse, ses constats, ses critères et ses limites. Pydantic refuse les champs inattendus et les valeurs hors des types prévus. Cela garantit une structure exploitable, pas la vérité du contenu.

## 7 Correspondance avec votre schéma

| Élément initial | Version GitHub |
|---|---|
| Jira | OpenProject Community Edition |
| Sources de code | API GitHub, dépôt et Pull Request |
| Orchestrateur et agents 1 à 7 | Implémentés en Python |
| Documentation et connaissances | Fichier de standards versionné, fourni explicitement |
| Tests et analyse statique | Workflows GitHub Actions et collecteur isolé |
| Modèle IA | Ollama local avec Qwen2.5-Coder |
| Commentaires | Synthèse générale dans la PR et le ticket |
| Rapport | Markdown et JSON |
| Traçabilité | Identifiant d'exécution, date, SHA et SQLite |
| Tableau de bord | Streamlit facultatif |
| Réanalyse après correction | Nouvelle commande ou surveillance périodique |
| Validation et fusion | Approbation humaine dans GitHub |
| Clôture du ticket | Manuelle dans OpenProject |

Il n'y a pas de recherche RAG dans les revues passées, de webhook, de récupération automatique des artefacts, de revue inline ou de fusion autonome dans cette version.

## 8 Dépannage

| Symptôme | Vérification et action |
|---|---|
| `ModuleNotFoundError: pydantic` | Activez le bon environnement puis exécutez `python -m pip install -e .` |
| Le service OpenProject ne répond pas | Attendez la fin de l'initialisation et consultez les journaux du conteneur |
| Erreur API 401 ou 403 | Vérifiez le jeton, le compte de service et ses permissions sur ce projet ou dépôt |
| Erreur API 404 | Vérifiez le nom du propriétaire, le dépôt et les identifiants numériques |
| Ollama indisponible | Vérifiez son démarrage, le port 11434 et le modèle présent dans `ollama list` |
| Agent `incomplete` | Vérifiez mémoire, délai et validité de la réponse du modèle ; réduisez la PR puis relancez |
| Rapport du mauvais commit | Recollectez les preuves depuis le SHA actuel de la branche de PR |
| Dépôt non propre | Commitez ou retirez du clone jetable les changements non prévus ; n'écrasez pas votre travail personnel |
| Outil `error` | Vérifiez son installation dans le runner et sa configuration ; une absence n'est pas un succès |
| Tests `not_run` | La collecte n'a pas reçu `--run-tests` |
| Couverture inconnue | Vérifiez le module ciblé, pytest-cov et les rapports ; ne saisissez pas un taux arbitraire |
| Tableau de bord vide | Lancez une revue réelle ou activez l'affichage des simulations |
| Publication refusée | Le ticket ou la PR a changé ; refaites la revue sur la version actuelle |
| Publication incertaine | Cherchez le commentaire par identifiant de revue puis réconciliez le journal local |

Le programme évite d'imprimer les réponses brutes contenant potentiellement des secrets. Pour diagnostiquer un problème d'API, utilisez les journaux des services et un compte de test avec des droits limités.

## 9 Passer du laboratoire à une utilisation en équipe

Validez d'abord la solution sur un dépôt pilote. Constituez un petit jeu de PR avec des défauts connus et des changements corrects. Pour chaque agent, notez les problèmes réellement détectés, les faux positifs et les oublis. Ajustez les prompts, les seuils et le modèle à partir de ces résultats.

Déployez ensuite les services sur une infrastructure administrée avec HTTPS, gestion des comptes, sauvegardes et restauration testée. Remplacez l'OpenProject tout-en-un par l'installation officielle recommandée. Placez Ollama sur un réseau interne ; son API locale ne doit pas être exposée directement sur Internet. Le client fourni impose HTTPS en dehors de localhost.

Figez les versions de dépendances et les digests des images après vos essais. Le laboratoire emploie des plages de versions et certains tags flottants pour faciliter le démarrage. Enregistrez aussi la version et l'identifiant du modèle utilisé. Les températures basses ne rendent pas les modèles parfaitement déterministes.

Séparez le runner qui exécute le code du robot possédant les jetons. Le runner reçoit uniquement le dépôt à vérifier et les ressources de test nécessaires. Vérifiez la provenance des preuves avant leur import. Le masquage de quelques motifs de secrets dans le prototype réduit les fuites courantes ; il ne remplace pas un contrôle complet des données.

Conservez `runs/`, la base SQLite, les journaux de publication et les volumes des services selon une durée de conservation adaptée. Les rapports peuvent contenir des extraits de code. Pour sauvegarder SQLite, utilisez son mécanisme de sauvegarde ou arrêtez les écritures pendant la copie. Sauvegardez OpenProject selon sa procédure officielle ; conservez aussi une copie de vos dépôts Git et des données de revue dont vous avez besoin.

Pour plusieurs workers, remplacez l'historique et les petits journaux locaux par un stockage transactionnel et une file durable. Ajoutez une authentification au tableau de bord si vous l'ouvrez à une équipe. Les protections locales fournies ne constituent pas une plateforme multiutilisateur de production.

## 10 Critères de réussite du pilote

1. Vous créez un ticket OpenProject avec des critères compréhensibles.
2. Une PR GitHub correspond à ce ticket et possède un SHA identifiable.
3. Les outils produisent des preuves associées à ce SHA, dans un environnement isolé.
4. Les sept agents produisent un résultat ou signalent clairement leur échec.
5. Les résultats manquants ne deviennent jamais des validations favorables.
6. Le rapport expose les limites et distingue les constats du modèle de ceux des outils.
7. La publication de la synthèse fonctionne sur un dépôt de test.
8. Un nouveau commit rend nécessaire une nouvelle analyse.
9. Un réviseur humain approuve la bonne version avant fusion.
10. Le ticket est clôturé après vérification de la fusion.

## 11 Sources et fichiers de référence

- [API GitHub des Pull Requests et du diff](https://docs.github.com/en/rest/pulls/pulls).
- [API GitHub des commentaires](https://docs.github.com/en/rest/issues/comments).
- [Événements GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
- [Permissions GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).
- [Action checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), [upload-artifact](https://github.com/actions/upload-artifact).
- [OpenProject Community](https://www.openproject.org/fr/edition-community/), [installation Docker](https://www.openproject.org/docs/installation-and-operations/installation/docker/), [API](https://www.openproject.org/docs/api/introduction/).
- [Ollama et JSON structuré](https://docs.ollama.com/capabilities/structured-outputs), [modèle Qwen](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct).
- [Ruff](https://docs.astral.sh/ruff/integrations/), [Bandit](https://bandit.readthedocs.io/en/latest/man/bandit.html), [pytest](https://pytest.org/en/stable/how-to/output.html), [Gitleaks](https://github.com/gitleaks/gitleaks).

Le connecteur emploie la version d'API GitHub `2026-03-10`, configurable dans `.env`. Les actions utilisent des tags de version ; figez leurs SHA et les digests des conteneurs après votre recette. Une version choisie ici n'est pas une affirmation qu'il s'agit de la dernière version de chaque composant.
