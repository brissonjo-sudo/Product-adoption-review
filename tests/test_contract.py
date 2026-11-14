import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_plugin_and_skill_names_match(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        skill = (ROOT / "skills" / "product-adoption-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(manifest["name"], "product-adoption-review")
        self.assertIn("name: product-adoption-review", skill)

    def test_manifests_and_changelog_share_one_version(self) -> None:
        versions = {
            json.loads((ROOT / folder / "plugin.json").read_text(encoding="utf-8"))["version"]
            for folder in (".claude-plugin", ".codex-plugin")
        }
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        latest = re.search(r"^## \[([^\]]+)\]", changelog, re.MULTILINE)
        assert latest is not None
        self.assertEqual(versions, {latest.group(1)})

    def test_current_version_has_an_archived_evaluation(self) -> None:
        version = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        self.assertTrue((ROOT / "docs" / f"evaluation-{version}.md").exists())

    def test_readmes_link_each_other_and_open_a_feedback_channel(self) -> None:
        french = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("(README.en.md)", french)
        self.assertIn("(README.md)", english)
        for text in (french, english):
            self.assertIn("J+7" if text is french else "Day 7", text)

    def test_each_decision_is_defined_in_the_rubric(self) -> None:
        rubric = (
            ROOT / "skills" / "product-adoption-review" / "references" / "review-rubric.md"
        ).read_text(encoding="utf-8")
        for decision in ("- `GO` :", "- `GO conditionnel` :", "- `NO-GO` :"):
            self.assertIn(decision, rubric)
        self.assertIn("avant la diffusion", rubric)

    def test_description_names_triggers_and_fits_the_limit(self) -> None:
        skill = (ROOT / "skills" / "product-adoption-review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        description = re.search(r'^description: "(.+)"$', skill, re.MULTILINE)
        assert description is not None
        self.assertLessEqual(len(description.group(1)), 1024)
        for trigger in ("évaluer", "release", "GO / NO-GO"):
            self.assertIn(trigger, description.group(1))

    def test_skill_is_implicitly_discoverable_but_scoped(self) -> None:
        config = (ROOT / "skills" / "product-adoption-review" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        skill = (ROOT / "skills" / "product-adoption-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", config)
        self.assertIn("Ne pas", skill)
        self.assertIn("développement interne", skill)

    def test_audit_contract_captures_stage_and_evidence_quality(self) -> None:
        skill = (ROOT / "skills" / "product-adoption-review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("assisted-pilot", skill)
        self.assertIn("contradictory", skill)
        self.assertIn("issue-id", skill)
        self.assertIn("test-de-non-régression", skill)


if __name__ == "__main__":
    unittest.main()
