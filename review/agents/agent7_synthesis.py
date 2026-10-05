"""Agent 7 : résumé rédactionnel et recommandation déterministe séparée."""
from .common import analyze


def run(context, model, results):
    result = analyze(model, 7,
        "Synthétise les six analyses en français : risques prioritaires, actions concrètes et incertitudes. "
        "Ne crée pas de nouveaux constats ; laisse findings et criteria vides. "
        "Ne déclare jamais une fusion approuvée. Le programme calculera la recommandation.",
        {"agents": [r.model_dump() for r in results], "warnings": context.warnings})
    result.findings = []
    result.criteria = []
    return result


def recommendation(context, results):
    corrections, missing = [], []
    if context.demo:
        missing.append("Démonstration simulée : aucune revue réelle.")
    for result in results:
        if result.status != "complete":
            missing.append(f"Agent {result.agent} incomplet.")
        if any(f.severity in ("high", "critical") for f in result.findings):
            corrections.append(f"Constat majeur de l'agent {result.agent} à vérifier et corriger.")
    compliance = next((r for r in results if r.agent == 4), None)
    if not compliance or not compliance.criteria or any(c.status == "unknown" for c in compliance.criteria):
        missing.append("Critères d'acceptation absents ou partiellement inconnus.")
    if compliance and any(c.status == "not_met" for c in compliance.criteria):
        corrections.append("Au moins un critère paraît non satisfait.")
    evidence = context.evidence
    for name in ("ruff", "pytest", "bandit", "gitleaks"):
        tool = evidence.tools.get(name) if evidence else None
        if not tool or tool.status in ("error", "not_run"):
            missing.append(f"Preuve {name} absente ou inexploitable.")
        elif tool.status == "failed" or tool.total_findings > 0 or tool.findings:
            corrections.append(f"Contrôle {name} avec écarts.")
    if not evidence or evidence.coverage_percent is None:
        missing.append("Couverture inconnue.")
    elif evidence.coverage_percent < 80:
        corrections.append("Couverture de lignes inférieure au seuil pédagogique de 80 %.")
    if not evidence or evidence.tests_run - evidence.tests_skipped <= 0:
        missing.append("Aucun test effectivement exécuté.")
    if evidence and evidence.tests_failed:
        corrections.append("Des tests ont échoué.")
    if context.warnings:
        missing.extend(context.warnings)
    if corrections:
        return "corrections_recommandees", corrections + missing
    if missing:
        return "revue_humaine_requise", missing
    return "pret_pour_validation_humaine", ["Contrôles disponibles satisfaits ; approbation humaine obligatoire."]
