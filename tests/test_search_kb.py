import contextlib
import io
import json
import subprocess
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import search_kb  # noqa: E402


class SearchKnowledgeBaseTests(unittest.TestCase):
    def test_resolve_resource_under_cli_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            resource_dir = (
                root
                / "@deveco"
                / "deveco-cli"
                / "node_modules"
                / "@deveco"
                / "deveco-cli-knowledgebase"
            )
            resource_dir.mkdir(parents=True)
            docs_path = resource_dir / "docs.zip"
            docs_path.write_bytes(b"test")

            search_kb._candidate_roots.cache_clear()
            with patch.dict(
                "os.environ",
                {"DEVECO_CLI_ROOT": str(root)},
                clear=False,
            ):
                resolved = search_kb._resolve_resource("docs.zip", "UNUSED_ENV")
            search_kb._candidate_roots.cache_clear()

            self.assertEqual(str(docs_path), resolved)

    def test_zip_search_returns_matching_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_path = Path(tmpdir) / "docs.zip"
            with zipfile.ZipFile(docs_path, "w") as archive:
                archive.writestr(
                    "guides/arkts.md",
                    "# ArkTS\nUse RelationalStore for persistent data.\n",
                )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                search_kb.search_zip(
                    str(docs_path),
                    ["RelationalStore"],
                    limit=3,
                    max_files=15,
                    context=1,
                )

            result = output.getvalue()
            self.assertIn("guides/arkts.md", result)
            self.assertIn("RelationalStore", result)

    def test_sqlite_search_uses_detected_text_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            db_path = root / "search.db"
            connection = sqlite3.connect(db_path)
            connection.execute(
                "CREATE TABLE documents (doc_title TEXT, search_text TEXT)"
            )
            connection.execute(
                "INSERT INTO documents (doc_title, search_text) VALUES (?, ?)",
                ("Data Guide", "Use RelationalStore for persistent data."),
            )
            connection.commit()
            connection.close()

            index_path = root / "index.zip"
            with zipfile.ZipFile(index_path, "w") as archive:
                archive.write(db_path, "search.db")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                search_kb.search_sqlite(
                    str(index_path),
                    ["RelationalStore"],
                    max_files=15,
                    limit=3,
                )

            result = output.getvalue()
            self.assertIn("[documents#", result)
            self.assertIn("RelationalStore", result)

    def test_cli_json_keeps_results_when_one_resource_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs_path = root / "docs.zip"
            with zipfile.ZipFile(docs_path, "w") as archive:
                archive.writestr("guides/page.md", "# 页面\n页面生命周期\n")
            completed = subprocess.run(
                [sys.executable, search_kb.__file__, "-k", "页面", "--mode", "both",
                 "--format", "json", "--docs-path", str(docs_path),
                 "--index-path", str(root / "missing.zip")],
                check=True, capture_output=True, encoding="utf-8",
            )
        report = json.loads(completed.stdout)
        docs, index = report["searches"]
        self.assertEqual(docs["results"][0]["path"], "guides/page.md")
        self.assertIn("页面", docs["results"][0]["matches"][0]["snippet"])
        self.assertEqual(index["result_count"], 0)
        self.assertIn("DEVECO_CLI_INDEX", index["error"])

    def test_missing_resources_have_actionable_errors(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            search_kb.search_zip(None, ["ArkTS"], 3, 15, 1)
            search_kb.search_sqlite(None, ["ArkTS"], 15, 3)

        result = output.getvalue()
        self.assertIn("DEVECO_CLI_DOCS", result)
        self.assertIn("DEVECO_CLI_INDEX", result)


if __name__ == "__main__":
    unittest.main()

