from ..models import AgentResult


def analyze(model, number, instruction, payload):
    try:
        return model.analyze(number, instruction, payload)
    except Exception as exc:
        # Un échec reste visible ; pas de résultat favorable par défaut.
        return AgentResult(agent=number, status="incomplete", summary="Analyse non terminée.",
            limitations=[f"Échec {type(exc).__name__} ; vérifier le service et relancer."])


def code_payload(context):
    return {"diff": context.diff, "standards": context.standards,
            "head_sha": context.head_sha, "scope": context.warnings}


def append_tools(result, context, names):
    for name in names:
        tool = context.evidence.tools.get(name) if context.evidence else None
        if not tool or tool.status in ("not_run", "error"):
            result.limitations.append(f"{name} non exécuté ou en erreur.")
        if tool:
            # Les constats déterministes ne dépendent pas de la fidélité du résumé du modèle.
            result.findings.extend(tool.findings[:40])
            if tool.total_findings > 40:
                result.limitations.append(f"{name} : seuls 40 constats affichés sur {tool.total_findings}.")
    return result
