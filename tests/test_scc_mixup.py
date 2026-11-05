"""SCC donor selection and TensorFlow mixing regression tests."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

NOTEBOOK = Path(__file__).resolve().parents[1] / 'notebooks/16_scc_mixup_training.ipynb'

def helpers(**extra):
    scope = dict(np=np, pd=pd, **extra)
    for cell in json.loads(NOTEBOOK.read_text())['cells']:
        if cell['cell_type'] != 'code':
            continue
        for node in ast.parse(''.join(cell['source'])).body:
            if isinstance(node, ast.FunctionDef) and node.name in {'donor_positions', 'read_resized', 'mix_training_view'}:
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<mixup helper>', 'exec'), scope)
    return scope

class MixUpTests(unittest.TestCase):
    def test_donors_are_distinct_scc_in_same_dataset_and_different_known_group(self):
        rows = pd.DataFrame([
            ('PAD', 'A', 'a', 'SCC', 'one'), ('PAD', 'B', 'b', 'SCC', 'one'),
            ('PAD', 'C', 'c', 'SCC', 'two'), ('PAD', 'D', 'd', 'BCC', 'three'),
            ('MILK', 'E', 'e', 'SCC', 'four'),
        ], columns=['dataset', 'image_id', 'image_hash', 'class_label', 'group_id'], index=[4, 7, 8, 9, 14])
        fn = helpers()['donor_positions']
        donors = fn(rows, 42)
        np.testing.assert_array_equal(donors[:2], [2, 2])
        self.assertIn(donors[2], [0, 1])
        np.testing.assert_array_equal(donors[3:], [3, 4])
        np.testing.assert_array_equal(donors, fn(rows, 42))

    @unittest.skipUnless(importlib.util.find_spec('tensorflow'), 'TensorFlow available in CI')
    def test_tf_zip_mixes_eligible_image_and_keeps_ineligible_image(self):
        import tensorflow as tf
        with tempfile.TemporaryDirectory() as directory:
            anchor = str(Path(directory) / 'anchor.png')
            donor = str(Path(directory) / 'donor.png')
            tf.io.write_file(anchor, tf.io.encode_png(tf.zeros((2, 2, 3), tf.uint8)))
            tf.io.write_file(donor, tf.io.encode_png(tf.fill((2, 2, 3), tf.constant(200, tf.uint8))))
            h = helpers(tf=tf, IMAGE_SIZE=(2, 2), SEED=42, MIX_MIN=.25, MIX_MAX=.25, MIX_RATE=1.)
            ds = tf.data.Dataset.from_tensor_slices(([anchor, anchor], [donor, donor], [1., 0.], [True, False]))
            draws = tf.data.Dataset.random(seed=13, rerandomize_each_iteration=True)
            result = list(tf.data.Dataset.zip((ds, draws)).map(h['mix_training_view']).as_numpy_iterator())
            np.testing.assert_allclose(result[0][0], 50.)
            np.testing.assert_allclose(result[1][0], 0.)
            self.assertEqual([row[1] for row in result], [1., 0.])

if __name__ == '__main__':
    unittest.main()
