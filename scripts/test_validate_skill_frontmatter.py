import tempfile
import unittest
from pathlib import Path

from validate_skill_frontmatter import frontmatter_errors, skill_files


class SkillFrontmatterTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def _write_skill(self, name, frontmatter, directory=None):
        path = self.root / "skills" / (directory or name) / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n\nBody.\n", encoding="utf-8")
        return path

    def test_accepts_valid_frontmatter(self):
        path = self._write_skill(
            "fallow-review",
            "name: fallow-review\ndescription: Review changed code before merge.",
        )
        self.assertEqual(frontmatter_errors(path), [])

    def test_rejects_colon_in_plain_scalar_description(self):
        # Regression for the report that `npx skills add` refused the skill:
        # a plain scalar containing ": " parses as a nested mapping, not text.
        path = self._write_skill(
            "fallow-review",
            "name: fallow-review\ndescription: Drives a loop: fetch the guide, return a judgment.",
        )
        self.assertTrue(
            any("not valid YAML" in error for error in frontmatter_errors(path)),
            frontmatter_errors(path),
        )

    def test_accepts_colon_inside_block_scalar_description(self):
        path = self._write_skill(
            "fallow-review",
            "name: fallow-review\ndescription: >-\n  Drives a loop: fetch the guide, return a judgment.",
        )
        self.assertEqual(frontmatter_errors(path), [])

    def test_reports_missing_frontmatter(self):
        path = self.root / "skills" / "fallow" / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("No frontmatter here.\n", encoding="utf-8")
        self.assertEqual(frontmatter_errors(path), [f"{path}: missing frontmatter"])

    def test_reports_missing_description(self):
        path = self._write_skill("fallow", "name: fallow")
        self.assertIn(f"{path}: missing 'description' in frontmatter", frontmatter_errors(path))

    def test_reports_name_directory_mismatch(self):
        path = self._write_skill(
            "fallow",
            "name: fallow\ndescription: Codebase intelligence.",
            directory="fallow-analysis",
        )
        self.assertIn(
            f"{path}: name 'fallow' does not match directory 'fallow-analysis'",
            frontmatter_errors(path),
        )

    def test_reports_non_kebab_name(self):
        path = self._write_skill(
            "Fallow_Review",
            "name: Fallow_Review\ndescription: Review changed code.",
        )
        self.assertIn(
            f"{path}: name 'Fallow_Review' must be lowercase letters, numbers, and hyphens",
            frontmatter_errors(path),
        )

    def test_skips_vendored_directories(self):
        self._write_skill("fallow", "name: fallow\ndescription: Codebase intelligence.")
        vendored = self.root / "node_modules" / "other" / "SKILL.md"
        vendored.parent.mkdir(parents=True, exist_ok=True)
        vendored.write_text("---\nname: other\n---\n", encoding="utf-8")
        self.assertNotIn(vendored, skill_files(self.root))


if __name__ == "__main__":
    unittest.main()
