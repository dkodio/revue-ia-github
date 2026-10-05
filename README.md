# Revue de code avec GitHub et sept agents IA

Version 0.2.0 : GitHub pour les dépôts et Pull Requests, OpenProject pour les tickets, Ollama pour le modèle local et sept agents Python pour la revue.

Commencez par **GUIDE.html**, lisible dans un navigateur, ou par **[le guide détaillé](docs/GUIDE.md)**. Le guide contient l'installation en quatorze étapes et le code des sept agents. Les détails des workflows sont dans **[GitHub Actions](docs/GITHUB_ACTIONS.md)**.

## Essai immédiat sans GitHub ni modèle

```bash
git clone https://github.com/dkodio/revue-ia-github.git
cd revue-ia-github
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m review.cli demo
```

Le rapport simulé est enregistré dans `runs/IDENTIFIANT/`. Aucun service distant n'est contacté.

## Mode réel

```bash
python scripts/init_env.py
# Renseigner les jetons dans .env, puis démarrer OpenProject et Ollama.
python -m review.cli review --ticket 42 --repo dkodio/revue-ia-github --pr 1 \
  --evidence /CHEMIN/evidence.json --standards examples/STANDARDS.md
python -m review.cli publish runs/IDENTIFIANT/review.json
```

Le dépôt est `dkodio/revue-ia-github`. Remplacez les numéros de ticket et de Pull Request par les vôtres. Les publications sont explicites ; le code ne fusionne aucune PR.

## Contenu livré

- `review/agents/agent1_requirements.py` à `agent7_synthesis.py` : code des sept agents.
- `review/connectors.py` : API GitHub et OpenProject.
- `review/orchestrator.py`, `llm.py`, `models.py` : orchestration, Ollama et contrats JSON.
- `.github/workflows/tests.yml` : tests du robot sur GitHub Actions.
- `.github/workflows/evidence.yml` : contrôles et artefact associé au SHA exact de la PR.
- `.github/pull_request_template.md` : modèle de Pull Request.
- `scripts/collect_evidence.py`, `Dockerfile.runner`, `review/ci.py` : collecte et validation des preuves.
- `example_app/` et `tests/test_calculator.py` : application de démonstration et trois cas de test.
- `review/watch.py` : surveillance locale d'une PR GitHub.
- `dashboard.py` : tableau de bord local optionnel.
- `docs/VALIDATION.md` : vérifications réalisées et limites.

Les workflows sont conçus pour ce dépôt, avec le robot à la racine de la branche cible. Pour une autre application, adaptez les chemins et les dépendances selon le guide. Le transfert des preuves GitHub Actions vers le robot local reste manuel. La présence du code sur GitHub ne démarre pas OpenProject ni Ollama : suivez le guide pour installer ces services et renseigner vos jetons locaux.
