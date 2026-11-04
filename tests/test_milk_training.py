"""CPU checks for training-manifest guards, source hashes and per-class metrics."""
import ast
import hashlib
import io
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from PIL import Image, ImageOps
from sklearn.metrics import classification_report

NOTEBOOK = Path(__file__).resolve().parents[1] / 'notebooks' / '13_milk10k_model_training.ipynb'


def helpers():
    n = json.loads(NOTEBOOK.read_text())
    scope = dict(np=np, pd=pd, Image=Image, ImageOps=ImageOps, io=io, hashlib=hashlib,
                 classification_report=classification_report,
                 CLASS_NAMES=['BCC', 'Melanoma', 'SCC'], CLASS_TO_INDEX={'BCC': 0, 'Melanoma': 1, 'SCC': 2})
    for cell in n['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in {'validate_frame', 'reference_digest', 'score_table'}:
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<notebook helper>', 'exec'), scope)
    return scope


class MilkTrainingTests(unittest.TestCase):
    def setUp(self):
        self.h = helpers()

    def frame(self):
        return pd.DataFrame([dict(dataset='MILK10k', image_id=str(i), image_path=f'{i}.jpg',
                                  class_label=label, label_index=i, split='train')
                             for i, label in enumerate(self.h['CLASS_NAMES'])])

    def test_validation_rows_cannot_enter_training(self):
        frame = self.frame()
        frame.loc[0, 'split'] = 'validation'
        with self.assertRaises(ValueError):
            self.h['validate_frame'](frame, 'train', 'training')

    def test_changed_class_order_and_duplicate_ids_are_rejected(self):
        frame = self.frame()
        frame.loc[0, 'label_index'] = 2
        with self.assertRaises(ValueError):
            self.h['validate_frame'](frame, 'train', 'training')
        frame = self.frame()
        frame.loc[1, 'image_id'] = frame.loc[0, 'image_id']
        with self.assertRaises(ValueError):
            self.h['validate_frame'](frame, 'train', 'training')

    def test_original_pixel_and_external_byte_hashes(self):
        image = Image.new('RGB', (5, 9), 'red')
        exif = Image.Exif(); exif[274] = 6
        buffer = io.BytesIO(); image.save(buffer, format='JPEG', exif=exif)
        raw = buffer.getvalue()
        with Image.open(io.BytesIO(raw)) as im:
            rgb = ImageOps.exif_transpose(im).convert('RGB')
            legacy = hashlib.sha256(f'{rgb.width}x{rgb.height}:RGB:'.encode() + rgb.tobytes()).hexdigest()
        for dataset in ['HAM10000', 'PAD-UFES-20']:
            self.assertEqual(self.h['reference_digest'](raw, dataset), legacy)
        for dataset in ['MILK10k', 'Fitzpatrick17k']:
            self.assertEqual(self.h['reference_digest'](raw, dataset), hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            self.h['reference_digest'](raw, 'unknown')

    def test_macro_f1_exposes_complete_scc_failure(self):
        labels = np.array([0] * 10 + [1] * 10 + [2])
        scores = np.eye(3)[np.array([0] * 10 + [1] * 10 + [0])]
        metrics, table, predicted = self.h['score_table'](labels, scores)
        self.assertGreater(metrics['accuracy'], .95)
        self.assertEqual(metrics['SCC_recall'], 0)
        self.assertEqual(metrics['SCC_f1'], 0)
        self.assertLess(metrics['macro_f1'], .67)

    def test_invalid_score_rows_are_rejected(self):
        for scores in [np.array([[float('nan'), 0, 1]]), np.array([[1, 1, 1]]), np.array([[1, 0]])]:
            with self.assertRaises(ValueError):
                self.h['score_table'](np.array([0]), scores)


if __name__ == '__main__':
    unittest.main()
