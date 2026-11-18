import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ABSOLUTE_LOCAL_PATH = re.compile(r"(?:\b[A-Za-z]:\\|/Users/|/home/)")


class RepositoryTests(unittest.TestCase):
    def test_skill_frontmatter(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        frontmatter = content.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name:\s+harmonyos-capabilities\s*$")
        self.assertRegex(frontmatter, r"(?m)^description:\s+\S")

    def test_local_markdown_links_resolve(self):
        broken = []
        for markdown in ROOT.rglob("*.md"):
            content = markdown.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK.findall(content):
                target = raw_target.strip().strip("<>")
                if not target or target.startswith(("#", "mailto:")):
                    continue
                if "://" in target:
                    continue
                target = target.split("#", 1)[0]
                if not (markdown.parent / target).resolve().is_file():
                    broken.append(f"{markdown.relative_to(ROOT)} -> {target}")
        self.assertEqual([], broken)

    def test_no_machine_specific_absolute_paths(self):
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            if path.suffix.lower() not in {
                ".md",
                ".py",
                ".yaml",
                ".yml",
                ".txt",
            }:
                continue
            content = path.read_text(encoding="utf-8")
            if ABSOLUTE_LOCAL_PATH.search(content):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_large_upstream_manual_snapshots_are_not_vendored(self):
        forbidden = [
            ROOT / "references" / "devecocli-readme.md",
            ROOT / "references" / "devecocli-skill.md",
            ROOT / "references" / "agent-layer.md",
        ]
        self.assertEqual([], [str(path) for path in forbidden if path.exists()])


if __name__ == "__main__":
    unittest.main()

