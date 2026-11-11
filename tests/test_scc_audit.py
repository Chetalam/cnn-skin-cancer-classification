import ast
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

class SCCAuditTests(unittest.TestCase):
    def setUp(self):
        notebook = json.loads((ROOT / 'notebooks/08_scc_decision_and_fitzpatrick_audit.ipynb').read_text())
        self.env = {'np': np, 'pd': pd, 'CLASSES': ['BCC', 'Melanoma', 'SCC']}
        for cell in notebook['cells']:
            if cell['cell_type'] != 'code': continue
            tree = ast.parse(''.join(cell['source']))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    exec(compile(ast.Module(body=[node], type_ignores=[]), '<audit>', 'exec'), self.env)

    def test_reported_experiment_six_counts(self):
        matrix=np.array([[178, 7, 12], [13, 169, 0], [19, 0, 10]])
        labels=[]; predictions=[]
        for actual in range(3):
            for predicted in range(3):
                labels.extend([actual]*matrix[actual,predicted])
                predictions.extend([predicted]*matrix[actual,predicted])
        table=self.env['class_metrics'](np.array(labels), np.array(predictions))
        self.assertAlmostEqual(table.f1.mean(), .7369946052167543)
        self.assertEqual(int(table.iloc[2].tp),10)
        self.assertAlmostEqual(table.iloc[2].recall,10/29)

    def test_unknown_phototypes_are_preserved_and_no_cross_dataset_match(self):
        self.env['lookup']=pd.DataFrame({'dataset':['PAD-UFES-20'], 'image_id':['same.png'], 'recorded_fitzpatrick':['5']})
        frame=pd.DataFrame({'dataset':['HAM10000','PAD-UFES-20'], 'image_id':['same.png','same.png']})
        result=self.env['attach_phototype'](frame)
        self.assertEqual(result.phototype_group.tolist(), ['Unknown','IV-VI'])

    def test_absent_classes_are_undefined_and_small_groups_flagged(self):
        frame=pd.DataFrame({'class_label':['BCC'], 'prediction':['BCC'], 'recorded_fitzpatrick':['5'], 'phototype_group':['IV-VI']})
        rows=self.env['subgroup_metrics'](frame,'prediction','validation','baseline')
        for row in rows:
            self.assertTrue(row['insufficient_support'])
            if row['class_label'] != 'BCC':
                self.assertIsNone(row['recall'])
                self.assertIsNone(row['f1'])
