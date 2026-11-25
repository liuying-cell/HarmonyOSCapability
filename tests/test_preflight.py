import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doctor


class PreflightTests(unittest.TestCase):
    def test_doctor_reports_missing_tools_and_knowledge_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(doctor.shutil, "which", return_value=None), patch.object(
                doctor, "_resolve_resource", return_value=None
            ):
                report = doctor.build_report(tmpdir, skip_devices=False)
        self.assertFalse(report["cli"]["available"])
        self.assertFalse(report["deveco_code"]["available"])
        self.assertNotIn("devices", report)
        self.assertIn("offline knowledge base incomplete", report["warnings"])
        self.assertEqual(report["knowledge_base"], {
            "docs_path": None, "docs_exists": False,
            "index_path": None, "index_exists": False,
        })

    def test_project_snapshot_reads_products_modules_and_abilities(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "build-profile.json5").write_text('''{
                // Representative DevEco build profile
                app: {
                    products: [{name: "default", targetSdkVersion: "6.0.0(20)"},],
                    signingConfigs: [{name: "default", material: {storePassword: "private"}}],
                },
                modules: [{name: "entry", srcPath: "./entry"}],
            }''', encoding="utf-8")
            module = root / "entry" / "src" / "main"
            module.mkdir(parents=True)
            (module / "module.json5").write_text(
                '{module: {name: "entry", type: "entry", abilities: [{name: "EntryAbility"}]}}',
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-S", str(SCRIPTS / "project_snapshot.py"), "--project", str(module),
                 "--format", "json"],
                check=True, capture_output=True, encoding="utf-8",
            )
            result = json.loads(completed.stdout)
            self.assertEqual(Path(result["project_root"]), root.resolve())
        self.assertEqual(result["build_profile"]["products"][0]["targetSdkVersion"], "6.0.0(20)")
        self.assertEqual(result["build_profile"]["signingConfigs"], ["default"])
        self.assertNotIn("private", completed.stdout)
        self.assertEqual(result["modules"][0]["abilities"][0]["name"], "EntryAbility")
