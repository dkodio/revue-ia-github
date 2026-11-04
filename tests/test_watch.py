import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
from threading import Event, Thread
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from apscheduler.events import EVENT_JOB_MAX_INSTANCES
from review import watch
from test_review import context, clean_evidence, results


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.args = argparse.Namespace(ticket=42, repo="team/calculator", pr=1,
                                       evidence=None, standards=None, interval=60,
                                       out=Path(self.tmp.name), publish=False, once=False)
        self.op, self.git = Mock(), Mock()
        self.model = Mock()
        self.model.name = "test-model"
        self.ctx = context()
        self.report = SimpleNamespace(run_id="test-run", results=results())
        self.fetch = self.patch("fetch_context", side_effect=lambda *args: self.ctx.model_copy(deep=True))
        self.run = self.patch("run", return_value=self.report)
        self.save = self.patch("save", return_value=self.args.out / "test-run")
        self.publish = self.patch("publish")
        output = redirect_stdout(StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)
        self.watcher = watch.Watch(self.args, self.op, self.git, self.model)

    def patch(self, name, **kwargs):
        patcher = patch.object(watch, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def test_first_cycle_then_unchanged_context_is_skipped(self):
        self.assertEqual(self.watcher.cycle(), 0)
        self.assertEqual(self.watcher.cycle(), 0)
        self.run.assert_called_once()
        self.publish.assert_not_called()
        self.assertEqual(json.loads(self.watcher.state_path.read_text())["run_id"], "test-run")

    def test_restart_uses_saved_fingerprint(self):
        self.watcher.cycle()
        restarted = watch.Watch(self.args, self.op, self.git, self.model)
        self.assertEqual(restarted.cycle(), 0)
        self.run.assert_called_once()

    def test_commit_change_triggers_new_review(self):
        self.watcher.cycle()
        self.ctx.head_sha = "c" * 40
        self.assertEqual(self.watcher.cycle(), 0)
        self.assertEqual(self.run.call_count, 2)

    def test_ticket_change_triggers_new_review(self):
        self.watcher.cycle()
        self.ctx.ticket_description = "Critère supplémentaire"
        self.assertEqual(self.watcher.cycle(), 0)
        self.assertEqual(self.run.call_count, 2)

    def test_new_matching_evidence_triggers_review(self):
        self.watcher.cycle()
        self.args.evidence = self.args.out / "evidence.json"
        self.args.evidence.write_text(clean_evidence().model_dump_json())
        self.assertEqual(self.watcher.cycle(), 0)
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(self.run.call_args.args[0].evidence.head_sha, self.ctx.head_sha)

    def test_stale_evidence_excluded(self):
        self.args.evidence = self.args.out / "evidence.json"
        self.args.evidence.write_text(clean_evidence(head_sha="c" * 40).model_dump_json())
        self.assertEqual(self.watcher.cycle(), 0)
        ctx = self.run.call_args.args[0]
        self.assertIsNone(ctx.evidence)
        self.assertIn("ancien commit", ctx.warnings[0])

    def test_incomplete_analysis_is_retried_without_publication(self):
        self.args.publish = True
        self.report.results[0].status = "incomplete"
        self.assertEqual(self.watcher.cycle(), 2)
        self.assertFalse(self.watcher.state_path.exists())
        self.publish.assert_not_called()
        self.report.results[0].status = "complete"
        self.op.ticket.return_value = {"subject": self.ctx.ticket_subject,
                                      "description": {"raw": self.ctx.ticket_description},
                                      "updatedAt": self.ctx.ticket_updated_at}
        self.assertEqual(self.watcher.cycle(), 0)
        self.assertEqual(self.run.call_count, 2)
        self.publish.assert_called_once()

    def test_collection_error_does_not_prevent_next_cycle(self):
        self.fetch.side_effect = [TimeoutError("indisponible"), self.ctx]
        self.assertEqual(self.watcher.cycle(), 2)
        self.run.assert_not_called()
        self.assertEqual(self.watcher.cycle(), 0)
        self.run.assert_called_once()

    def test_publication_failure_is_not_automatically_resent(self):
        self.args.publish = True
        self.publish.side_effect = TimeoutError("envoi incertain")
        self.assertEqual(self.watcher.cycle(), 2)
        self.assertTrue(self.watcher.state_path.exists())
        self.assertEqual(self.watcher.cycle(), 0)
        self.publish.assert_called_once()
        self.run.assert_called_once()

    def test_own_publication_update_is_absorbed(self):
        self.args.publish = True
        self.op.ticket.return_value = {"subject": self.ctx.ticket_subject,
                                      "description": {"raw": self.ctx.ticket_description},
                                      "updatedAt": "2026-11-04T12:00:00Z"}
        self.assertEqual(self.watcher.cycle(), 0)
        self.ctx.ticket_updated_at = "2026-11-04T12:00:00Z"
        self.assertEqual(self.watcher.cycle(), 0)
        self.run.assert_called_once()
        self.publish.assert_called_once()

    def test_once_returns_error_without_starting_scheduler(self):
        argv = ["watch", "--ticket", "42", "--repo", self.args.repo, "--pr", "1",
                "--out", str(self.args.out), "--once"]
        self.fetch.side_effect = TimeoutError("indisponible")
        with patch("sys.argv", argv), patch.object(watch, "load_env"), \
             patch.object(watch, "clients", return_value=(self.op, self.git)), \
             patch.object(watch, "required", return_value="test"), \
             patch.object(watch, "Ollama", return_value=self.model), \
             patch.object(watch, "create_scheduler") as factory:
            self.assertEqual(watch.main(), 2)
            factory.assert_not_called()
        self.fetch.assert_called_once()


class SchedulerTests(unittest.TestCase):
    def test_scheduler_configuration_and_immediate_first_cycle(self):
        watcher = Mock()
        scheduler = watch.create_scheduler(watcher, 60)
        job = scheduler.get_job("watch")
        self.assertEqual(job.trigger.interval.total_seconds(), 60)
        self.assertEqual(job.max_instances, 1)
        self.assertTrue(job.coalesce)
        self.assertEqual(job.misfire_grace_time, 60)
        self.assertLess(abs((job.next_run_time - watch.datetime.now(watch.timezone.utc)).total_seconds()), 2)
        watcher.cycle.assert_not_called()

    def test_interval_below_minimum_rejected(self):
        with self.assertRaisesRegex(ValueError, "30 secondes"):
            watch.create_scheduler(Mock(), 29)

    def test_real_scheduler_prevents_overlapping_cycles(self):
        started, release, skipped = Event(), Event(), Event()
        watcher = Mock()
        watcher.cycle.side_effect = lambda: (started.set(), release.wait(5))
        scheduler = watch.create_scheduler(watcher, 30)
        # Accelerate the trigger for this test, not the production CLI interval.
        scheduler.reschedule_job("watch", trigger="interval", seconds=0.05)
        scheduler.add_listener(lambda event: skipped.set(), EVENT_JOB_MAX_INSTANCES)
        thread_errors = []
        def start():
            try:
                scheduler.start()
            except Exception as exc:
                thread_errors.append(exc)
        thread = Thread(target=start, daemon=True)
        thread.start()
        try:
            self.assertTrue(started.wait(2), "Premier cycle non déclenché")
            self.assertTrue(skipped.wait(2), "Chevauchement non bloqué")
            self.assertEqual(watcher.cycle.call_count, 1)
        finally:
            release.set()
            if scheduler.running:
                scheduler.shutdown(wait=True)
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(thread_errors, [])


if __name__ == "__main__":
    unittest.main()
