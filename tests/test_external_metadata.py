import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / "scripts" / "audit_external_metadata.py"
spec = importlib.util.spec_from_file_location("external_audit", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExternalMetadata(unittest.TestCase):
    def test_preserves_group_codes_and_diagnoses(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "metadata.csv"
            file.write_text("disease,skin_tone,patient\nsquamous cell carcinoma,56,A\nsquamous cell carcinoma,56,A\nother malignant condition,34,B\n", encoding="utf-8")
            before = file.read_bytes()
            result = module.audit(file, "disease", "skin_tone", "patient")
            self.assertEqual(result["records"], 3)
            scc = next(row for row in result["counts"] if row["diagnosis"] == "squamous cell carcinoma")
            self.assertEqual(scc["recorded_skin_group"], "56")
            self.assertEqual(scc["recorded_patients"], 1)
            self.assertEqual(file.read_bytes(), before)
            self.assertNotIn("A", [str(row) for row in result["counts"]])


if __name__ == "__main__":
    unittest.main()
