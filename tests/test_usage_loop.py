import argparse
import importlib.util
import json
import os
import tempfile
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

    def args(self, index: int, project: str | None = None) -> argparse.Namespace:
        return argparse.Namespace(
            project_root=project or str(Path(self.temp.name) / f"project-{index % 2}"),
            artifact_kind="repository",
            trigger="publication README",
            finding=["promise|major|La promesse décrit le système plutôt que le résultat"],
            decision=["Montrer un avant-après avant l'architecture"],
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
        self.assertIn("Aucun fichier du skill officiel n'a été modifié", report)
        self.assertFalse(review_usage.generate()["generated"])

    def test_sensitive_values_are_rejected(self) -> None:
        args = self.args(1)
        args.decision = [r"Lire C:\\Users\\Jo\\secret.txt"]
        with self.assertRaises(ValueError):
            usage_log.record(args)

    def test_truncated_last_line_and_duplicate_are_tolerated(self) -> None:
        event = usage_log.record(self.args(1))
        log = Path(self.temp.name) / "usage.jsonl"
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            handle.write('{"truncated":')
        items = usage_log.read_jsonl(log)
        self.assertEqual(len(items), 1)

    def test_incomplete_use_does_not_advance_threshold(self) -> None:
        args = self.args(1)
        args.completed = False
        usage_log.record(args)
        self.assertEqual(usage_log.status()["total_completed"], 0)


if __name__ == "__main__":
    unittest.main()
