import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from docx import Document
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import inference
import explainability as xai
from branding import PROJECT_NAME
from referral_document import checklist_docx


def fixture():
    return dict(image_id=6,status='predicted',cancer_class='BCC',confidence=.8,
                scores={'BCC':.8,'Melanoma':.1,'SCC':.1},created_at=1730000000,
                model_name='ResNet50 / qa / '+'a'*64,image_sha256='b'*64,case_reference='QA sample only')


class Explanations(unittest.TestCase):
    def test_known_signal_localisation_without_modifying_input(self):
        rgb = np.zeros((14,14,3),dtype=np.float32)
        rgb[:7,:7] = 255
        original = rgb.copy()
        def score(batch):
            bcc = .2 + .6 * batch[:,:7,:7].mean(axis=(1,2,3))/255
            return np.column_stack((bcc,(1-bcc)/2,(1-bcc)/2))
        _, deltas = xai.occlusion_map(rgb,score,0,grid=2)
        self.assertGreater(deltas[0,0],0)
        self.assertEqual(np.count_nonzero(deltas),1)
        np.testing.assert_array_equal(rgb,original)
        self.assertEqual(Image.open(io.BytesIO(xai.overlay_png(rgb,deltas))).size,(14,14))

    def test_no_colour_for_constant_scores_or_numeric_noise(self):
        rgb=np.full((14,14,3),100,dtype=np.uint8)
        _, deltas=xai.occlusion_map(rgb,lambda b:np.tile([.8,.1,.1],(len(b),1)),0)
        for values in (deltas, np.full((7,7),.000001)):
            overlay=np.asarray(Image.open(io.BytesIO(xai.overlay_png(rgb,values))))
            np.testing.assert_array_equal(rgb,overlay)

    def test_invalid_model_output_rejected(self):
        for values in ([[.5,.5,.5]], [[np.nan,.1,.2]], [[-.1,.2,.9]], [[.8,.2]]):
            with self.assertRaises(ValueError):xai.validate_scores(values,1)

    def test_acknowledgement_requires_boolean_confirmation_before_loading(self):
        for answer in (False,None,'Yes',1):
            with patch.object(inference,'inspect_package') as inspect:
                with self.assertRaises(ValueError):
                    inference.predict_image(b'unused',lesion_confirmed=True,limitation_acknowledged=answer)
                inspect.assert_not_called()

    def test_original_image_rejected_before_loading(self):
        out=io.BytesIO();Image.new('RGB',(20,20)).save(out,format='PNG')
        with patch.object(xai,'inspect_package') as inspect:
            with self.assertRaisesRegex(ValueError,'exact original'):
                xai.explain_saved_image(out.getvalue(),fixture(),'b'*64)
            inspect.assert_not_called()

    def test_export_checks_prediction_identity_and_scores(self):
        p=fixture()
        e=dict(method=xai.METHOD,image_hash=p['image_sha256'],**{k:p[k] for k in ('image_id','model_name','cancer_class','scores')})
        xai.validate_explanation(e,p)
        for key,value in [('image_hash','wrong'),('image_id',7),('model_name','other'),('cancer_class','SCC'),('scores',{'BCC':.7,'Melanoma':.2,'SCC':.1})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                checklist_docx(p,explanation={**e,key:value})

    def test_word_has_project_identity_and_readable_sections(self):
        doc=Document(io.BytesIO(checklist_docx(fixture())))
        self.assertIn(PROJECT_NAME,'\n'.join(p.text for p in doc.paragraphs))
        self.assertIn('Review ID: 6',doc.sections[0].footer.paragraphs[0].text)
        self.assertEqual(len(doc.tables[0].rows),4)

    def test_acknowledgement_is_image_bound_and_bilingual(self):
        from streamlit.testing.v1 import AppTest
        from eligibility import classification_allowed, LIMITATION, ACKNOWLEDGEMENT
        self.assertFalse(classification_allowed('Not sure', True))
        self.assertFalse(classification_allowed('No lesion / normal skin', True))
        self.assertFalse(classification_allowed('Yes', False))
        self.assertFalse(classification_allowed('Yes', 1))
        self.assertTrue(classification_allowed('Yes', True))
        code = (
            "import streamlit as st\\n"
            "from eligibility import acknowledgement_control\\n"
            "st.write(acknowledgement_control('image_one'))"
        )
        at = AppTest.from_string(code).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.checkbox[0].value, False)
        self.assertEqual(at.checkbox[0].label, ACKNOWLEDGEMENT)
        self.assertTrue(any(LIMITATION in item.message for item in at.info))
        at.checkbox[0].check().run()
        self.assertEqual(at.checkbox[0].value, True)
        self.assertIn('True', at.markdown[-1].value)

        # A different upload gets a different, initially unchecked key.
        second = AppTest.from_string(code.replace('image_one', 'image_two')).run()
        self.assertEqual(second.checkbox[0].value, False)
        sw = AppTest.from_string(
            "import streamlit as st\\nst.session_state['app_language']='sw'\\n" + code
        ).run()
        self.assertFalse(sw.exception)
        self.assertEqual(
            sw.checkbox[0].label,
            'Ninaelewa kikomo hiki cha makundi matatu na kwamba matokeo si utambuzi wa ugonjwa.'
        )

    def test_tensorflow_serialized_model_and_historical_parity(self):
        import tensorflow as tf
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            inputs=tf.keras.Input((16,16,3))
            features=tf.keras.layers.GlobalAveragePooling2D()(inputs)
            outputs=tf.keras.layers.Dense(3,activation='softmax',kernel_initializer='zeros',bias_initializer=tf.keras.initializers.Constant([1.,0.,0.]))(features)
            tf.keras.Model(inputs,outputs).save(folder/'model.keras')
            checksum=inference._sha256(folder/'model.keras')
            meta=dict(model_name='ResNet50',run_id='synthetic_test_only',class_names=inference.CLASS_NAMES,model_sha256=checksum,image_size=[16,16],preprocessing='resnet50',preprocessing_location='outside saved model',decode='tf.io.decode_image channels=3; no EXIF orientation transform')
            (folder/'metadata.json').write_text(json.dumps(meta))
            output=io.BytesIO();Image.new('RGB',(20,24),(100,60,20)).save(output,format='PNG');raw=output.getvalue()
            with patch.dict(os.environ,{'SKIN_MODEL_DIR':tmp}):
                result=inference.predict_image(raw,lesion_confirmed=True,limitation_acknowledged=True)
                p={**fixture(),'scores':result['scores'],'confidence':result['scores']['BCC'],
                   'model_name':'ResNet50 / synthetic_test_only / '+checksum,'image_sha256':hashlib.sha256(raw).hexdigest()}
                explanation=xai.explain_saved_image(raw,p,p['image_sha256'])
                self.assertEqual(len(explanation['regions']),49)
                self.assertLess(explanation['max_abs_pp'],.01)
                doc=Document(io.BytesIO(checklist_docx(p,explanation)))
                self.assertEqual(len(doc.inline_shapes),1)
                with self.assertRaisesRegex(ValueError,'active model differs'):
                    xai.explain_saved_image(raw,{**p,'model_name':'other'},p['image_sha256'])
                with self.assertRaisesRegex(ValueError,'scores do not match'):
                    xai.explain_saved_image(raw,{**p,'scores':{'BCC':.8,'Melanoma':.1,'SCC':.1}},p['image_sha256'])
            inference._load_model.cache_clear()
