import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse
import numpy as np
from PIL import Image
import io

ROOT=Path(__file__).resolve().parents[1]
class ExternalTrainingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.env=dict(Path=Path,np=np,Image=Image,io=io,hashlib=hashlib,urlparse=urlparse,EXTERNAL_ROOT=self.root)
        notebook=json.loads((ROOT/'notebooks/09_external_clinical_data_training.ipynb').read_text())
        for cell in notebook['cells']:
            if cell['cell_type']!='code':continue
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node,ast.FunctionDef) and node.name in {'image_fingerprints','fetch_one'}:
                    exec(compile(ast.Module(body=[node],type_ignores=[]),'<external>', 'exec'),self.env)

    def test_cached_verified_image_resumes_without_network(self):
        output=io.BytesIO();Image.new('RGB',(20,20),'blue').save(output,format='JPEG')
        raw=output.getvalue();digest=hashlib.md5(raw).hexdigest()
        (self.root/(digest+'.jpg')).write_bytes(raw)
        result=self.env['fetch_one'](dict(md5hash=digest,url='https://www.dermaamin.com/example.jpg'))
        self.assertEqual(result['download_status'],'ok')
        self.assertEqual(result['image_hash'],hashlib.sha256(raw).hexdigest())

    def test_cache_corruption_is_rejected(self):
        digest='0'*32
        (self.root/(digest+'.jpg')).write_bytes(b'not an image')
        result=self.env['fetch_one'](dict(md5hash=digest,url='https://www.dermaamin.com/example.jpg'))
        self.assertEqual(result['download_status'],'failed')
        self.assertIn('MD5 mismatch',result['download_error'])

    def test_unexpected_source_host_is_rejected_without_download(self):
        result=self.env['fetch_one'](dict(md5hash='0'*32,url='https://example.org/file.jpg'))
        self.assertEqual(result['download_status'],'failed')
        self.assertIn('allowlisted',result['download_error'])
