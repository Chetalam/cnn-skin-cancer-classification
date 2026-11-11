import ast
import json
from pathlib import Path
import unittest


class NotebookSyntax(unittest.TestCase):
    def test_final_workflow_cells_parse(self):
        path = Path(__file__).resolve().parents[1] / "notebooks" / "07_final_training_and_evaluation.ipynb"
        self.check_notebook(path)
        self.check_notebook(path.with_name("08_scc_decision_and_fitzpatrick_audit.ipynb"))
        self.check_notebook(path.with_name("09_external_clinical_data_training.ipynb"))
        self.check_notebook(path.with_name("10_export_streamlit_model.ipynb"))

    def check_notebook(self, path):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                with self.subTest(cell=index):
                    ast.parse("".join(cell["source"]))


if __name__ == "__main__":
    unittest.main()
