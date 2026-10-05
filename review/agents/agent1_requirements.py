"""Agent 1 : transforme le ticket OpenProject en critères traçables."""
from .common import analyze


def run(context, model):
    return analyze(model, 1,
        "Extrais les exigences explicites et les critères d'acceptation. Attribue CA-1, CA-2, etc. "
        "Chaque critère cite un passage exact du ticket dans evidence et reste unknown. "
        "N'invente pas de besoin. Signale les ambiguïtés et contraintes. "
        "Si le ticket ne contient pas de critère vérifiable, laisse criteria vide.",
        {"subject": context.ticket_subject, "description": context.ticket_description})
