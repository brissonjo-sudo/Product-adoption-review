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
