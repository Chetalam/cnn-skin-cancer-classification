import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
APP=Path(__file__).resolve().parents[1]/'app'
sys.path.insert(0,str(APP))
import inference
import db

class PredictionAnalytics(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.original=db.DB_PATH;db.DB_PATH=Path(self.temp.name)/'test.db'
        self.addCleanup(setattr,db,'DB_PATH',self.original);db.initialize()
        password='Private test passphrase 123'
        self.worker=db.register('Worker','worker@clinic.test',password,'Clinic A')
        self.peer=db.register('Peer','peer@clinic.test',password,'Clinic A')
        self.outside=db.register('Other','other@clinic.test',password,'Clinic B')
        self.admin=db.register('Admin','admin@clinic.test',password,'Clinic A',requested_role='system_administrator')
        self.result=dict(scores={'BCC':.1,'Melanoma':.2,'SCC':.7},model_name='ResNet50',run_id='exp_test',model_sha256='b'*64,artifact_path='private/model.keras',preprocessing='test contract')
    def review(self,owner,key):
        return db.save_review(owner,key,'anonymous','sample.png',Image.new('RGB',(20,20)),'a'*64)
    def test_prediction_atomic_ownership_version_and_idempotency(self):
        image=self.review(self.worker,'one')
        with self.assertRaises(ValueError):db.record_prediction(self.outside,image,'a'*64,self.result)
        with self.assertRaises(ValueError):db.record_prediction(self.worker,image,'c'*64,self.result)
        self.assertEqual(db.prediction_detail(self.worker,image)['status'],'awaiting_model')
        db.record_prediction(self.worker,image,'a'*64,self.result)
        changed={**self.result,'run_id':'later','scores':{'BCC':.9,'Melanoma':.05,'SCC':.05}}
        db.record_prediction(self.worker,image,'a'*64,changed)
        detail=db.prediction_detail(self.worker,image)
        self.assertEqual(detail['cancer_class'],'SCC');self.assertEqual(detail['scores'],self.result['scores'])
        self.assertIn('exp_test',detail['model_name'])
        self.assertIn('exp_test',db.history(self.worker)[0]['model_name'])
        with db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM model_versions').fetchone()[0],1)
            self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
        db.delete_review(self.worker,image)
        with db.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM prediction_scores').fetchone()[0],3)
    def test_analytics_scope_and_no_personal_fields(self):
        image=self.review(self.worker,'one');self.review(self.peer,'two');self.review(self.outside,'three')
        db.record_prediction(self.worker,image,'a'*64,self.result)
        self.assertEqual(db.analytics(self.worker)['total'],1)
        self.assertEqual(db.analytics(self.admin)['total'],2)
        self.assertEqual(db.analytics(self.admin)['predicted'],1)
        self.assertEqual(db.analytics(self.admin)['classes'],{'SCC':1})
        self.assertEqual(db.analytics(self.admin,0,1)['total'],0)
        text=json.dumps(db.analytics(self.admin))
        self.assertNotIn('anonymous',text);self.assertNotIn('worker@clinic.test',text)
    def test_invalid_scores_leave_pending_without_partial_rows(self):
        image=self.review(self.worker,'one')
        for scores in [{'BCC':float('nan'),'Melanoma':0.,'SCC':1.}, {'BCC':.5,'Melanoma':.5,'SCC':.5}]:
            with self.assertRaises(ValueError):db.record_prediction(self.worker,image,'a'*64,{**self.result,'scores':scores})
        self.assertEqual(db.prediction_detail(self.worker,image)['scores'],{})
        with db.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM model_versions').fetchone()[0],0)

class InferenceContract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name);artifact=self.folder/'model.keras';artifact.write_bytes(b'test artifact')
        self.meta=dict(model_name='ResNet50',run_id='test',class_names=inference.CLASS_NAMES,
                       model_sha256=inference._sha256(artifact),image_size=[224,224],preprocessing='resnet50',
                       preprocessing_location='outside saved model',decode='tf.io.decode_image channels=3; no EXIF orientation transform')
        self.save();self.env=patch.dict(os.environ,{'SKIN_MODEL_DIR':str(self.folder)});self.env.start();self.addCleanup(self.env.stop)
    def save(self): (self.folder/'metadata.json').write_text(json.dumps(self.meta))
    def test_rejects_checksum_class_order_and_preprocessing(self):
        original=dict(self.meta)
        for key,value in [('model_sha256','0'*64),('class_names',['SCC','BCC','Melanoma']),('preprocessing','other')]:
            self.meta={**original,key:value};self.save()
            with self.assertRaises(ValueError):inference.inspect_package()
    def test_inference_preserves_scores_and_model_provenance(self):
        class FakeModel:
            input_shape=(None,224,224,3);output_shape=(None,3)
            def __call__(self,inputs,training=False):return np.array([[.1,.8,.1]])
        out=io.BytesIO();Image.new('RGB',(10,10)).save(out,format='PNG')
        with patch.object(inference,'_load_model',return_value=(FakeModel(),threading.Lock())),patch.object(inference,'prepare_image',return_value=np.zeros((1,224,224,3))):
            result=inference.predict_image(out.getvalue(), lesion_confirmed=True)
        self.assertEqual(result['scores']['Melanoma'],.8)
        self.assertEqual(result['model_sha256'],self.meta['model_sha256'])
    def test_mismatched_metrics_cannot_be_displayed_as_active_results(self):
        (self.folder/'test_metrics.json').write_text(json.dumps({'source_run_id':'other','model_sha256':'wrong'}))
        with self.assertRaises(ValueError):inference.evaluation_metrics()


class VisibilityGate(unittest.TestCase):
    def test_unconfirmed_images_do_not_reach_model_loading(self):
        for answer in [False, None, 'Yes', 1]:
            with self.subTest(answer=answer), patch.object(inference, '_load_model') as loader:
                with self.assertRaisesRegex(ValueError, 'clearly visible lesion'):
                    inference.predict_image(b'unused', lesion_confirmed=answer)
                loader.assert_not_called()
