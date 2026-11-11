"""CPU checks for MILK image fingerprinting and prospective split assignment."""
import ast
import hashlib
import io
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from PIL import Image


NOTEBOOK = Path(__file__).resolve().parents[1] / 'notebooks' / '12_milk10k_image_preparation.ipynb'


def helpers():
    notebook = json.loads(NOTEBOOK.read_text())
    scope = {'np': np, 'pd': pd, 'Image': Image, 'io': io, 'hashlib': hashlib,
             'CLASSES': ['BCC', 'Melanoma', 'SCC'], 'byte_seen': {}, 'pixel_seen': {}, 'dh_seen': []}
    names = {'fingerprints', 'remember', 'duplicate_match', 'assign_splits'}
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<notebook helper>', 'exec'), scope)
    return scope


class MilkPreparationTests(unittest.TestCase):
    def test_reencoded_pixels_are_detected(self):
        h = helpers()
        image = Image.fromarray(np.random.default_rng(42).integers(0, 255, (32, 32, 3), dtype=np.uint8))
        first, second = io.BytesIO(), io.BytesIO()
        image.save(first, format='PNG', compress_level=0)
        image.save(second, format='PNG', compress_level=9)
        a, b = h['fingerprints'](first.getvalue()), h['fingerprints'](second.getvalue())
        self.assertNotEqual(a['image_hash'], b['image_hash'])
        h['remember'](a, 'original:test_image')
        self.assertEqual(h['duplicate_match'](b), ('decoded_pixel_duplicate', 'original:test_image'))

    def test_near_duplicate_is_conservatively_flagged(self):
        h = helpers()
        h['remember']({'image_hash': 'a', 'pixel_hash': 'a', 'dhash': '0'}, 'paired_dermoscopic')
        self.assertEqual(h['duplicate_match']({'image_hash': 'b', 'pixel_hash': 'b', 'dhash': '15'}),
                         ('possible_near_duplicate', 'paired_dermoscopic'))
        self.assertEqual(h['duplicate_match']({'image_hash': 'c', 'pixel_hash': 'c', 'dhash': '31'}), (None, None))

    def test_split_is_deterministic_stratified_and_order_independent(self):
        h = helpers()
        frame = pd.DataFrame([{'isic_id': f'{label}_{i:03}', 'class_label': label}
                              for label in h['CLASSES'] for i in range(100)])
        a = h['assign_splits'](frame)
        b = h['assign_splits'](frame.sample(frac=1, random_state=17))
        pd.testing.assert_frame_equal(a, b)
        counts = pd.crosstab(a.class_label, a.split)
        self.assertTrue(counts.train.eq(70).all())
        self.assertTrue(counts.validation.eq(15).all())
        self.assertTrue(counts.test.eq(15).all())
        self.assertFalse(a.isic_id.duplicated().any())

    def test_small_class_blocks_split_export(self):
        h = helpers()
        frame = pd.DataFrame([{'isic_id': str(i), 'class_label': 'BCC'} for i in range(10)])
        with self.assertRaises(ValueError):
            h['assign_splits'](frame)


if __name__ == '__main__':
    unittest.main()
