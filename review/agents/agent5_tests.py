"""Agent 5 : analyse les preuves de tests, ne lance pas de code de PR."""
from .common import analyze, code_payload


def run(context, model, requirements):
    payload = code_payload(context)
    payload["criteria"] = [c.model_dump() for c in requirements.criteria]
    payload["test_evidence"] = context.evidence.model_dump() if context.evidence else None
    return analyze(model, 5,
        "Évalue les cas de tests visibles et propose des cas nominaux, limites et d'erreur précis. "
        "Les seuls tests exécutés sont ceux du rapport fourni, lié au commit. "
        "La couverture absente est inconnue, jamais 100 %. La couverture de lignes ne prouve pas "
        "la conformité métier. Ne présente jamais tes propositions comme exécutées.", payload)
