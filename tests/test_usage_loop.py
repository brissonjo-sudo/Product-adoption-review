import argparse
import importlib.util
import json
import os
import subprocess
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
            {
                "PRODUCT_ADOPTION_REVIEW_STATE_DIR": self.temp.name,
                "LOCALAPPDATA": str(Path(self.temp.name) / "localappdata"),
            },
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

    def test_status_warns_about_unmigrated_legacy_journal(self) -> None:
        legacy = (
            Path(os.environ["LOCALAPPDATA"])
            / "Packages" / "OpenAI.Codex_test" / "LocalCache" / "Local"
            / "Codex" / "product-adoption-review"
        )
        legacy.mkdir(parents=True)
        event = usage_log.record(self.args(1))
        self.assertNotIn("legacy_state_dir", usage_log.status())
        old = dict(event, usage_id="ancien-usage")
        (legacy / "usage.jsonl").write_text(json.dumps(old) + "\n", encoding="utf-8")
        state = usage_log.status()
        self.assertEqual(state["legacy_state_dir"], str(legacy))
        self.assertEqual(state["legacy_unmigrated_events"], 1)
        usage_log.append_jsonl(Path(self.temp.name) / "usage.jsonl", old)  # copie faite
        self.assertNotIn("legacy_state_dir", usage_log.status())

    def test_review_event_stores_a_relative_report_path(self) -> None:
        for index in range(10):
            usage_log.record(self.args(index))
        review_usage.generate()
        events = usage_log.read_jsonl(Path(self.temp.name) / "review-events.jsonl")
        self.assertEqual(events[0]["report"], "reviews/0001-0010.md")

    def test_issues_lists_vocabulary_then_journal_ids(self) -> None:
        args = self.args(1)
        args.finding = ["custom-gap|install|minor|observed|current|false|Écart local"]
        args.improvement = ["custom-gap|Corriger|Tester"]
        usage_log.record(args)
        usage_log.record(self.args(2))
        rows = {row["issue_id"]: row for row in usage_log.issues()["issues"]}
        self.assertTrue(set(usage_log.KNOWN_ISSUE_IDS) <= set(rows))
        self.assertTrue(rows["release-evidence-mismatch"]["known"])
        self.assertEqual(rows["release-evidence-mismatch"]["occurrences"], 1)
        self.assertFalse(rows["custom-gap"]["known"])
        self.assertEqual(rows["custom-gap"]["projects"], 1)
        self.assertEqual(rows["artifact-unavailable"]["occurrences"], 0)
        # Ajouté après la revue acceptée du bilan 0001-0010.
        self.assertTrue(rows["demo-missing"]["known"])
        # Ajoutés après la revue acceptée du bilan 0011-0020.
        for issue_id in (
            "personal-data-in-public-repo",
            "install-prerequisite-unverified",
            "docs-out-of-sync",
            "distribution-status-ambiguity",
        ):
            self.assertTrue(rows[issue_id]["known"])

    def test_record_signals_new_issue_ids_only_once(self) -> None:
        self.assertEqual(usage_log.record(self.args(1))["new_issue_ids"], [])
        args = self.args(2)
        args.finding = ["custom-gap|install|minor|observed|current|false|Écart local"]
        args.improvement = ["custom-gap|Corriger|Tester"]
        self.assertEqual(usage_log.record(args)["new_issue_ids"], ["custom-gap"])
        self.assertEqual(usage_log.record(args)["new_issue_ids"], [])

    def test_pattern_split_across_two_batches_is_promoted(self) -> None:
        # Lot 1 : deux occurrences dans deux projets ; lot 2 : une troisième.
        noise = self.args(0)
        noise.finding = []
        noise.improvement = []
        for index in range(20):
            if index in (0, 1, 12):
                usage_log.record(self.args(index))
            else:
                usage_log.record(noise)
        first = Path(review_usage.generate()["report"]).read_text(encoding="utf-8")
        self.assertIn("Aucun motif n'atteint le seuil", first)
        second = Path(review_usage.generate()["report"]).read_text(encoding="utf-8")
        self.assertIn("### `release-evidence-mismatch`", second)
        self.assertIn("(cumul depuis l'usage 1) : 3 / 2", second)

    def test_decision_is_recorded_without_moving_the_counter(self) -> None:
        for index in range(10):
            usage_log.record(self.args(index))
        review_usage.generate()
        self.assertEqual(usage_log.status()["undecided_reviews"], ["0001-0010"])
        review_usage.decide("0001-0010", "accepted", "Motifs revus avec Jo")
        state = usage_log.status()
        self.assertEqual(state["accepted_reviews"], ["0001-0010"])
        self.assertEqual(state["undecided_reviews"], [])
        self.assertEqual(state["reported_completed"], 10)
        self.assertEqual(state["next_review_at"], 20)

    def test_decision_on_unknown_batch_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            review_usage.decide("0001-0010", "accepted", "Aucun bilan")
        for index in range(10):
            usage_log.record(self.args(index))
        review_usage.generate()
        with self.assertRaises(ValueError):
            review_usage.decide("0001-0010", "maybe", "Décision invalide")

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

    def _input_file(self, **overrides) -> Path:
        data = dict(vars(self.args(1)), **overrides)
        path = Path(self.temp.name) / "record.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_record_from_input_file_matches_cli_contract(self) -> None:
        path = self._input_file()
        with patch("builtins.print"):
            self.assertEqual(usage_log.main(["record", "--input", str(path)]), 0)
        events = usage_log.read_jsonl(Path(self.temp.name) / "usage.jsonl")
        self.assertEqual(events[0]["findings"][0]["issue_id"], "release-evidence-mismatch")
        self.assertEqual(events[0]["target_stage"], "stable-release")

    def test_input_file_refuses_invented_or_missing_fields(self) -> None:
        for path in (
            self._input_file(artifact_type="repository"),
            self._input_file(outcome=None),
            self._input_file(finding="pas une liste"),
        ):
            with self.subTest(path=path.read_text(encoding="utf-8")[:40]), patch("builtins.print"):
                self.assertEqual(usage_log.main(["record", "--input", str(path)]), 1)
        self.assertEqual(usage_log.read_jsonl(Path(self.temp.name) / "usage.jsonl"), [])

    def test_input_file_cannot_be_mixed_with_inline_options(self) -> None:
        path = self._input_file()
        with self.assertRaises(SystemExit), patch("sys.stderr"):
            usage_log.main(["record", "--input", str(path), "--outcome", "GO"])

    def test_scripts_run_in_isolated_python_mode(self) -> None:
        for script in ("review_usage.py", "usage_log.py"):
            argv = [sys.executable, "-I", str(SCRIPTS / script)]
            if script == "usage_log.py":
                argv.append("status")
            # -I ignore les variables PYTHON*, pas celle de l'état : l'isolement du test tient.
            completed = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
            with self.subTest(script=script):
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertTrue(json.loads(completed.stdout)["ok"])

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
