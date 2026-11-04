# Vérifications et périmètre du prototype

## Résultats obtenus

**69 tests automatisés passent**, avec Python 3.12.14, Pydantic 2.14.1 et APScheduler 3.11.3 (vérification locale du 4 novembre 2026). La démonstration de la chaîne complète a également été exécutée, avec création d'un rapport Markdown, d'un JSON contenant les sept résultats et d'un historique SQLite exportable en CSV.

Les tests vérifient notamment les preuves manquantes, un commit incorrect, les tests tous ignorés, une couverture insuffisante, les erreurs du modèle, les critères oubliés, les changements de PR pendant la lecture, la protection contre les redirections de jetons et la reprise d'une publication incertaine.

Les tests ajoutés pour GitHub vérifient les en-têtes d'authentification et de version d'API, le type de contenu du diff, le chemin des commentaires, le journal de publication, le refus d'anciens rapports et la validation des artefacts. Les fichiers YAML ont été analysés syntaxiquement. Les déclencheurs, les permissions en lecture seule et les chemins des workflows ont aussi été contrôlés sans exécution distante.

La collecte des rapports Ruff, Bandit, Gitleaks et pytest est testée avec des sorties simulées. Les connecteurs API sont testés avec des objets simulés. Ces tests vérifient le comportement du programme ; ils ne constituent pas une validation contre les services externes.

## Ce qui reste à vérifier sur votre infrastructure

| Élément | État de validation |
|---|---|
| Sept agents et recommandation | Tests unitaires et démonstration exécutés |
| Rapports et historique SQLite | Création et export exécutés |
| Analyse des preuves | Tests sur rapports simulés exécutés |
| Appels OpenProject et GitHub | Contrats comparés aux documentations et tests simulés ; intégration réelle à réaliser |
| Appels Ollama | Schéma et gestion des erreurs testés ; génération réelle à réaliser |
| Services Docker Compose | Configuration fournie ; Docker absent dans l'environnement de préparation |
| Runner Docker et analyseurs | Code fourni ; construction et exécution réelles à réaliser |
| GitHub Actions | Syntaxe et propriétés des workflows contrôlées ; aucune exécution sur GitHub effectuée |
| Surveillance périodique APScheduler | Cycles avec services simulés et non-chevauchement avec le véritable ordonnanceur testés ; intégration avec les services réels à réaliser |
| Tableau de bord Streamlit | Code fourni ; Streamlit non installé dans l'environnement de préparation |
| Guide HTML | Structure, liens internes et code inclus contrôlés ; aperçu visuel non validé |

La prévisualisation des fichiers locaux avait été refusée par la politique du navigateur intégré lors de la préparation de la première version. Le guide GitHub a été contrôlé structurellement, sans nouvelle tentative de contourner cette restriction. Vous pouvez ouvrir le guide téléchargé dans votre navigateur.

## Limites d'exploitation

La revue est fondée sur le diff et un fichier explicite de standards. Elle n'analyse pas tous les fichiers du dépôt, ne garantit pas l'exactitude des observations du modèle et ne constitue pas un audit de sécurité complet. Les critères du ticket et les numéros de ligne restent à vérifier par le réviseur.

La publication ajoute des commentaires généraux, pas des annotations de lignes. Il n'y a ni fusion automatique, ni changement de statut du ticket, ni envoi de courriel implémenté. La surveillance utilise une interrogation périodique, pas des webhooks. L'historique SQLite et les journaux sont destinés à un petit pilote avec un seul opérateur.

Les preuves GitHub Actions doivent être téléchargées manuellement avant leur import local. Le workflow de collecte est préparé pour la structure du dépôt livré et analyse `example_app` par défaut avec Ruff et Bandit. Une application existante peut demander une adaptation des chemins et des dépendances.

Les fichiers de preuves sont associés à un SHA mais ne sont pas signés. Le masquage des secrets est partiel. Une utilisation en équipe demande une validation des permissions, de la provenance des preuves, de l'isolation du runner, des sauvegardes et des versions choisies.

## Reproduire les vérifications du programme

```bash
python -m unittest discover -s tests -v
python -m review.cli demo
python -m review.cli export --out historique.csv
```

La simulation ne se connecte à aucun service et refuse sa propre publication. Le code source livré est sous licence MIT ; les composants tiers gardent leurs propres licences.

## Intégration APScheduler

La boucle d’attente de `review/watch.py` est remplacée par APScheduler 3.11.3. Un premier cycle est planifié immédiatement, puis les cycles sont déclenchés toutes les 60 secondes par défaut (minimum 30). `max_instances=1` interdit le chevauchement de cette tâche dans le même processus ; `coalesce=True` regroupe les échéances manquées et la tolérance de retard est égale à l’intervalle. Le mode `--once` conserve un seul cycle sans démarrer l’ordonnanceur.

Les 14 nouveaux tests couvrent notamment le contexte inchangé et l’état conservé au redémarrage, les changements de commit et de ticket, les preuves nouvelles ou périmées, les analyses incomplètes, les erreurs de collecte, la publication incertaine, la prise en compte de notre propre commentaire et le mode ponctuel. Un test exécute réellement APScheduler avec un cycle bloqué et constate que la tentative suivante est refusée tant que ce cycle reste actif. Le regroupement est contrôlé dans la configuration de la tâche.

Ces résultats concernent cette modification locale : ils ne constituent pas un résultat GitHub Actions de la nouvelle version, ni une revue réelle avec Ollama et OpenProject. Les autres étapes de validation décrites plus haut restent distinctes.
