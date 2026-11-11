"""Public archive integrity and corrected-partition selection; no network in tests."""
import ast
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.request
import numpy as np
import pandas as pd
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
class ExternalTrainingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.env=dict(Path=Path,np=np,pd=pd,Image=Image,io=io,hashlib=hashlib,urllib=__import__('urllib'))
        n=json.loads((ROOT/'notebooks/09_external_clinical_data_training.ipynb').read_text())
        for cell in n['cells']:
            if cell['cell_type']!='code':continue
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node,ast.FunctionDef) and node.name in {'file_md5','download_verified','image_fingerprints','select_training_records'}:
                    exec(compile(ast.Module(body=[node],type_ignores=[]),'<public archive>','exec'),self.env)

    def test_cached_verified_file_avoids_network(self):
        target=self.root/'archive.zip';raw=b'fixture';target.write_bytes(raw)
        with patch('urllib.request.urlopen') as opener:
            self.env['download_verified']('https://zenodo.org/fixture',target,hashlib.md5(raw).hexdigest())
            opener.assert_not_called()

    def test_bad_download_cannot_become_verified_archive(self):
        target=self.root/'archive.zip'
        with patch('urllib.request.urlopen',return_value=io.BytesIO(b'wrong content')):
            with self.assertRaises(ValueError):self.env['download_verified']('https://zenodo.org/fixture',target,'0'*32)
        self.assertFalse(target.exists())
        self.assertTrue(target.with_suffix('.zip.part').exists())

    def test_corrected_holdout_disagreements_and_changed_labels_are_excluded(self):
        original=pd.DataFrame([
            dict(md5hash=str(i),label='squamous cell carcinoma',fitzpatrick_scale=5,fitzpatrick_centaur=5 if i!=3 else 2)
            for i in range(5)])
        clean=pd.DataFrame([
            dict(md5hash=str(i),label='squamous cell carcinoma' if i!=4 else 'melanoma',fst=5,partition='train' if i!=1 else 'test',new_img_name=str(i)+'.jpg')
            for i in range(5)])
        clean.loc[2,'partition']='val'
        selected=self.env['select_training_records'](original,clean)
        self.assertEqual(selected.md5hash.tolist(),['0'])
        self.assertEqual(selected.class_label.tolist(),['SCC'])
