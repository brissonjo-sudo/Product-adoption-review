import argparse
import importlib.util
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "product-adoption-review" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


usage_log = load_module("usage_log", SCRIPTS / "usage_log.py")
import sys

sys.modules["usage_log"] = usage_log
review_usage = load_module("review_usage", SCRIPTS / "review_usage.py")


class UsageLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {"PRODUCT_ADOPTION_REVIEW_STATE_DIR": self.temp.name},
            clear=False,
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def args(
        self,
        index: int,
        project: str | None = None,
        summary: str = "La preuve publiée ne correspond pas à la version courante",
        severity: str = "major",
        reproducible: bool = False,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            project_root=project or str(Path(self.temp.name) / f"project-{index % 2}"),
            artifact_kind="repository",
            trigger="publication README",
            audience="utilisateurs externes pilotes",
            channel="release publique",
            target_stage="stable-release",
            finding=[
                "release-evidence-mismatch|evidence|"
                f"{severity}|observed|current|{str(reproducible).lower()}|{summary}"
            ],
            improvement=[
                "release-evidence-mismatch|Relier la release à la preuve de la même version|"
                "Échouer si version et preuve divergent"
            ],
            decision=["Aligner l'artefact et sa preuve avant diffusion"],
            verification=["README relu statiquement"],
            outcome="audit livré",
            completed=True,
        )

    def test_review_is_generated_on_tenth_completed_use(self) -> None:
        for index in range(9):
            usage_log.record(self.args(index))
        self.assertFalse(review_usage.generate()["generated"])
        usage_log.record(self.args(9))
        result = review_usage.generate()
        self.assertTrue(result["generated"])
        report = Path(result["report"]).read_text(encoding="utf-8")
        self.assertIn("0001-0010", report)
        self.assertIn("release-evidence-mismatch", report)
        self.assertIn("Changement minimal proposé", report)
        self.assertIn("Échouer si version et preuve divergent", report)
        self.assertIn("ne représentent", report)
        self.assertIn("Aucun fichier du skill officiel n'a été modifié", report)
        self.assertFalse(review_usage.generate()["generated"])

    def test_default_state_dir_is_the_same_on_every_system(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PRODUCT_ADOPTION_REVIEW_STATE_DIR", None)
            os.environ.pop("XDG_DATA_HOME", None)
            expected = Path.home() / ".local" / "share" / "product-adoption-review"
            self.assertEqual(usage_log.state_dir(), expected)
            os.environ["XDG_DATA_HOME"] = self.temp.name
            self.assertEqual(
                usage_log.state_dir(), Path(self.temp.name) / "product-adoption-review"
            )

    def test_review_event_stores_a_relative_report_path(self) -> None:
        for index in range(10):
            usage_log.record(self.args(index))
        review_usage.generate()
        events = usage_log.read_jsonl(Path(self.temp.name) / "review-events.jsonl")
        self.assertEqual(events[0]["report"], "reviews/0001-0010.md")

    def test_equivalent_findings_are_grouped_by_stable_issue_id(self) -> None:
        summaries = [
            "La preuve publiée ne correspond pas au candidat",
            "Published evidence covers an earlier release",
            "Le rapport concerne une version antérieure",
        ]
        projects = [
            str(Path(self.temp.name) / "project-a"),
            str(Path(self.temp.name) / "project-b"),
            str(Path(self.temp.name) / "project-a"),
        ]
        for index, summary in enumerate(summaries):
            usage_log.record(self.args(index, project=projects[index], summary=summary))
        candidates = review_usage._candidate_findings(
            usage_log.read_jsonl(Path(self.temp.name) / "usage.jsonl")
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["issue_id"], "release-evidence-mismatch")
        self.assertEqual(candidates[0]["occurrences"], 3)
        self.assertEqual(candidates[0]["projects"], 2)

    def test_single_blocker_requires_reproducibility_for_promotion(self) -> None:
        event = usage_log.record(self.args(1, severity="blocker", reproducible=False))
        self.assertEqual(review_usage._candidate_findings([event]), [])
        reproducible = usage_log.record(
            self.args(2, severity="blocker", reproducible=True)
        )
        candidates = review_usage._candidate_findings([reproducible])
        self.assertEqual([item["issue_id"] for item in candidates], ["release-evidence-mismatch"])

    def test_reproducible_minor_does_not_promote_unreproduced_blocker(self) -> None:
        blocker = usage_log.record(self.args(1, severity="blocker", reproducible=False))
        minor = usage_log.record(self.args(2, severity="minor", reproducible=True))
        self.assertEqual(review_usage._candidate_findings([blocker, minor]), [])

    def test_legacy_events_in_journal_remain_grouped(self) -> None:
        legacy = {
            "project_id": "p1",
            "findings": [
                {"category": "promise", "severity": "major", "summary": "Promesse floue"}
            ],
        }
        grouped = review_usage._group_findings([legacy, dict(legacy, project_id="p2")])
        self.assertEqual(len(grouped), 1)
        self.assertTrue(grouped[0]["issue_id"].startswith("legacy-"))
        self.assertEqual(grouped[0]["occurrences"], 2)
        self.assertEqual(grouped[0]["evidence_statuses"], ["unverified"])

    def test_legacy_finding_format_is_refused_for_new_records(self) -> None:
        with self.assertRaises(ValueError):
            usage_log.parse_finding("promise|major|La promesse décrit le système")

    def test_more_than_four_findings_are_refused(self) -> None:
        args = self.args(1)
        args.finding = [
            f"issue-{i}|install|minor|observed|current|false|résumé {i}" for i in range(5)
        ]
        args.improvement = [f"issue-{i}|changer|tester" for i in range(5)]
        with self.assertRaises(ValueError):
            usage_log.record(args)

    def test_non_positive_threshold_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            usage_log.status(0)

    def test_sensitive_values_are_rejected(self) -> None:
        args = self.args(1)
        args.decision = [r"Lire C:\\Users\\Jo\\secret.txt"]
        with self.assertRaises(ValueError):
            usage_log.record(args)

    def test_known_secret_and_personal_formats_are_rejected(self) -> None:
        values = [
            "clé sk-proj-AbCdEfGh1234567890XyZ",
            "sk-ant-api03-AbCdEfGh1234567890",
            "AKIAIOSFODNN7EXAMPLE",
            "contact jean.dupont@exemple.fr",
            "voir /var/www/client-x/app",
            "voir ~/projets/client-x",
            r"\\serveur\partage\dossier",
        ]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                usage_log._safe_text(value, "decision")

    def test_public_url_without_query_is_accepted(self) -> None:
        url = "https://github.com/o/r/releases"
        self.assertEqual(usage_log._safe_text(url, "channel"), url)
        with self.assertRaises(ValueError):
            usage_log._safe_text(url + "?token=x", "channel")

    def test_truncated_last_line_and_duplicate_are_tolerated(self) -> None:
        event = usage_log.record(self.args(1))
        log = Path(self.temp.name) / "usage.jsonl"
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            handle.write('{"truncated":')
        items = usage_log.read_jsonl(log)
        self.assertEqual(len(items), 1)

    def test_records_after_interrupted_write_remain_readable(self) -> None:
        usage_log.record(self.args(1))
        log = Path(self.temp.name) / "usage.jsonl"
        with log.open("a", encoding="utf-8") as handle:
            handle.write('{"truncated":')
        usage_log.record(self.args(2))
        usage_log.record(self.args(3))
        self.assertEqual(len(usage_log.read_jsonl(log)), 3)
        self.assertEqual(usage_log.status()["total_completed"], 3)

    def test_valid_last_line_without_newline_is_kept(self) -> None:
        event = usage_log.record(self.args(1))
        log = Path(self.temp.name) / "usage.jsonl"
        log.write_text(json.dumps(event, ensure_ascii=False), encoding="utf-8")
        usage_log.record(self.args(2))
        self.assertEqual(len(usage_log.read_jsonl(log)), 2)

    def test_stale_lock_is_removed(self) -> None:
        lock = Path(self.temp.name) / ".write.lock"
        lock.write_text("", encoding="utf-8")
        old = time.time() - usage_log.STALE_LOCK_SECONDS - 1
        os.utime(lock, (old, old))
        usage_log.record(self.args(1))
        self.assertFalse(lock.exists())

    def test_recent_lock_still_blocks(self) -> None:
        lock = Path(self.temp.name) / ".write.lock"
        lock.write_text("", encoding="utf-8")
        with self.assertRaises(TimeoutError):
            with usage_log._lock(Path(self.temp.name), timeout=0.1):
                pass
        self.assertTrue(lock.exists())

    def test_incomplete_use_does_not_advance_threshold(self) -> None:
        args = self.args(1)
        args.completed = False
        usage_log.record(args)
        self.assertEqual(usage_log.status()["total_completed"], 0)

    def test_new_finding_requires_matching_improvement(self) -> None:
        args = self.args(1)
        args.improvement = []
        with self.assertRaises(ValueError):
            usage_log.record(args)

    def test_duplicate_problem_cannot_inflate_audit_count(self) -> None:
        args = self.args(1)
        args.finding *= 2
        with self.assertRaises(ValueError):
            usage_log.record(args)

    def test_existing_duplicate_findings_count_once_per_use(self) -> None:
        first = usage_log.record(self.args(1))
        first["findings"] *= 2
        second = usage_log.record(self.args(2))
        self.assertEqual(review_usage._candidate_findings([first, second]), [])
        self.assertEqual(review_usage._group_findings([first, second])[0]["occurrences"], 2)

    def test_go_without_findings_is_valid(self) -> None:
        args = self.args(1)
        args.finding = []
        args.improvement = []
        args.outcome = "GO pour remise documentaire"
        event = usage_log.record(args)
        self.assertEqual(event["findings"], [])
        self.assertEqual(event["improvements"], [])


if __name__ == "__main__":
    unittest.main()
