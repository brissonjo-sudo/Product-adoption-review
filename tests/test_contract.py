import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_plugin_and_skill_names_match(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        skill = (ROOT / "skills" / "product-adoption-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(manifest["name"], "product-adoption-review")
        self.assertIn("name: product-adoption-review", skill)

    def test_skill_is_implicitly_discoverable_but_scoped(self) -> None:
        config = (ROOT / "skills" / "product-adoption-review" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        skill = (ROOT / "skills" / "product-adoption-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", config)
        self.assertIn("Ne pas", skill)
        self.assertIn("développement interne", skill)


if __name__ == "__main__":
    unittest.main()
