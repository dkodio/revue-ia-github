"""Surveillance facultative d'une association ticket/PR, planifiée par APScheduler."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

from .cli import clients
from .config import load_env, required
from .connectors import fetch_context
from .llm import Ollama
from .ci import read_evidence
from .orchestrator import run
from .report import save
from .publish import publish
from .security import redact


def fingerprint(context, model_name):
    return hashlib.sha256((model_name + context.model_dump_json()).encode()).hexdigest()


class Watch:
    """Un cycle de surveillance et son état, indépendants du calendrier."""

    def __init__(self, args, op, git, model):
        self.args = args
        self.op = op
        self.git = git
        self.model = model
        args.out.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(f"{args.repo}:{args.pr}:{args.ticket}".encode()).hexdigest()[:16]
        self.state_path = args.out / f"watch-{key}.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

    def cycle(self):
        """Exécuter une seule vérification ; une erreur permet un prochain essai."""
        args = self.args
        try:
            standards = args.standards.read_text() if args.standards else ""
            ctx = fetch_context(self.op, self.git, args.ticket, args.repo, args.pr, standards)
            if args.evidence and args.evidence.exists():
                evidence = read_evidence(args.evidence)
                if evidence.head_sha == ctx.head_sha:
                    ctx.evidence = evidence
                else:
                    ctx.warnings.append("Les preuves locales portent sur un ancien commit et sont exclues.")
            digest = fingerprint(ctx, self.model.name)
            if self.state.get("digest") == digest:
                return 0
            report = run(ctx, self.model)
            dest = save(report, args.out)
            print(f"Rapport créé : {dest}", flush=True)
            if any(r.status != "complete" for r in report.results):
                print("Analyse incomplète ; une nouvelle tentative aura lieu au prochain cycle.", flush=True)
                return 2
            # Enregistrer avant la publication pour ne pas multiplier les envois en cas de panne.
            self.state = {"digest": digest, "run_id": report.run_id}
            self.state_path.write_text(json.dumps(self.state), encoding="utf-8")
            if args.publish:
                publish(report, self.op, self.git, dest / "publication.json")
                # Notre commentaire peut modifier updatedAt. Absorber seulement notre propre écriture.
                fresh = self.op.ticket(args.ticket)
                if fresh["subject"] == ctx.ticket_subject and (fresh.get("description", {}).get("raw") or "") == ctx.ticket_description:
                    ctx.ticket_updated_at = fresh["updatedAt"]
                    self.state["digest"] = fingerprint(ctx, self.model.name)
                    self.state_path.write_text(json.dumps(self.state), encoding="utf-8")
            return 0
        except Exception as exc:
            print(f"Cycle interrompu : {redact(str(exc))[:300]}. Vérifier le rapport et le journal avant une publication manuelle.", flush=True)
            return 2


def create_scheduler(watch, interval):
    """Une seule tâche active par processus ; pas de rafale après une échéance manquée."""
    if interval < 30:
        raise ValueError("L'intervalle minimal est de 30 secondes")
    scheduler = BlockingScheduler(timezone=timezone.utc,
                                  executors={"default": ThreadPoolExecutor(max_workers=1)})
    scheduler.add_job(watch.cycle, "interval", seconds=interval,
                      id="watch", max_instances=1, coalesce=True,
                      misfire_grace_time=interval,
                      next_run_time=datetime.now(timezone.utc))
    return scheduler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ticket", type=int, required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--pr", type=int, required=True)
    p.add_argument("--evidence", type=Path)
    p.add_argument("--standards", type=Path)
    p.add_argument("--interval", type=int, default=60)
    p.add_argument("--out", type=Path, default=Path("runs"))
    p.add_argument("--publish", action="store_true", help="Publier automatiquement la synthèse, sans approuver la PR")
    p.add_argument("--once", action="store_true")
    args = p.parse_args()
    if args.interval < 30:
        p.error("L'intervalle minimal est de 30 secondes")
    load_env()
    op, git = clients()
    model = Ollama(required("OLLAMA_URL"), required("OLLAMA_MODEL"), int(os.getenv("OLLAMA_TIMEOUT", "300")))
    watch = Watch(args, op, git, model)
    if args.once:
        return watch.cycle()
    scheduler = create_scheduler(watch, args.interval)
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Surveillance arrêtée.")
    finally:
        # Laisser finir le cycle actif pour préserver rapports et journal de publication.
        if scheduler.running:
            scheduler.shutdown(wait=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
