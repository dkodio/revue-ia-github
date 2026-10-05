"""Connecteurs explicites : aucune URL du ticket ou du modèle n'est suivie."""
import base64
import re
from .http import Client
from .models import Context


def repo_path(repository: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or any(x in (".", "..") for x in repository.split("/")):
        raise ValueError("Le dépôt doit avoir la forme proprietaire/depot")
    return "/repos/" + repository


class OpenProject:
    def __init__(self, url, token):
        auth = base64.b64encode(("apikey:" + token).encode()).decode()
        self.http = Client(url, {"Authorization": "Basic " + auth})

    def ticket(self, ticket_id):
        return self.http.request("GET", f"/api/v3/work_packages/{int(ticket_id)}")

    def comment(self, ticket_id, text):
        return self.http.request("POST", f"/api/v3/work_packages/{int(ticket_id)}/activities", {"comment": {"raw": text}})


class GitHub:
    def __init__(self, url, token, api_version="2026-03-10"):
        self.http = Client(url, {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": api_version,
            "User-Agent": "revue-ia-github/0.2.0",
        })

    def pull(self, repository, pr):
        return self.http.request("GET", f"{repo_path(repository)}/pulls/{int(pr)}")

    def diff(self, repository, pr):
        # GitHub renvoie le diff sur le même endpoint, selon l'en-tête Accept.
        return self.http.request("GET", f"{repo_path(repository)}/pulls/{int(pr)}",
                                 as_text=True, accept="application/vnd.github.diff")

    def comment(self, repository, pr, text):
        return self.http.request("POST", f"{repo_path(repository)}/issues/{int(pr)}/comments", {"body": text})


def fetch_context(op, git, ticket_id, repository, pr, standards="", evidence=None):
    ticket = op.ticket(ticket_id)
    before = git.pull(repository, pr)
    if before.get("state") != "open" or before.get("merged"):
        raise ValueError("La demande de fusion doit être ouverte")
    diff = git.diff(repository, pr)
    after = git.pull(repository, pr)
    for branch in ("head", "base"):
        if before[branch]["sha"] != after[branch]["sha"]:
            raise ValueError("Le code a changé pendant la lecture. Relancez la revue.")
    if len(diff) > 45_000:
        raise ValueError("Diff supérieur à 45 000 caractères ; découpez la PR. Aucune troncature silencieuse.")
    if len(ticket.get("description", {}).get("raw", "") or "") > 15_000:
        raise ValueError("Description du ticket trop longue ; maximum 15 000 caractères")
    if len(standards) > 10_000:
        raise ValueError("Standards trop longs ; maximum 10 000 caractères")
    return Context(ticket_id=ticket_id, ticket_subject=ticket["subject"],
        ticket_description=ticket.get("description", {}).get("raw", "") or "",
        ticket_updated_at=ticket["updatedAt"], repository=repository, pr=pr,
        head_sha=before["head"]["sha"], base_sha=before["base"]["sha"],
        pr_title=before["title"], diff=diff, standards=standards, evidence=evidence,
        warnings=["Analyse du diff uniquement : fichiers inchangés, binaires et contexte du dépôt non inspectés."])
