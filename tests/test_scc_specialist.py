"""Routing, selection and independent specialist-backbone regression checks."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

NOTEBOOK=Path(__file__).resolve().parents[1]/'notebooks'/'15_scc_bcc_specialist_training.ipynb'

def helpers(tf=None):
    scope={'np':np,'pd':pd,'CLASS_NAMES':['BCC','Melanoma','SCC'],'tf':tf}
    for cell in json.loads(NOTEBOOK.read_text())['cells']:
        if cell['cell_type']!='code':continue
        for node in ast.parse(''.join(cell['source'])).body:
            if isinstance(node,ast.FunctionDef) and node.name in {'combine_predictions','class_metrics','validation_objective','build_specialist','validate_manifest'}:
                exec(compile(ast.Module(body=[node],type_ignores=[]),'<helper>','exec'),scope)
    return scope

class SpecialistTests(unittest.TestCase):
    def test_routing_preserves_melanoma_and_can_recover_scc(self):
        h=helpers();base=np.array([[.05,.9,.05],[.7,.1,.2],[.2,.1,.7]])
        original=base.copy()
        predicted=h['combine_predictions'](base,[.99,.8,.2])
        np.testing.assert_array_equal(predicted,[1,2,0])
        np.testing.assert_array_equal(base,original)

    def test_calling_every_nonmelanoma_scc_does_not_meet_targets(self):
        h=helpers();base=np.eye(3)
        result=h['combine_predictions'](base,[1,1,1])
        metrics,_,_=h['class_metrics']([0,1,2],result)
        _,passed,preserves=h['validation_objective']({'original':metrics,'MILK10k':metrics})
        self.assertEqual(metrics['SCC_recall'],1)
        self.assertFalse(passed);self.assertFalse(preserves)

    def test_one_source_cannot_hide_failure_on_the_other(self):
        h=helpers();good=dict(accuracy=.9,macro_f1=.9,BCC_recall=.9,Melanoma_recall=.9,SCC_recall=.9,SCC_f1=.9)
        bad={**good,'SCC_recall':.2,'SCC_f1':.3}
        _,passed,_=h['validation_objective']({'original':good,'MILK10k':bad})
        self.assertFalse(passed)
        score,passed,preserves=h['validation_objective']({'original':good,'MILK10k':good})
        self.assertTrue(passed);self.assertTrue(preserves);self.assertAlmostEqual(score,6.9)

    def test_invalid_scores_and_training_split_are_rejected(self):
        h=helpers()
        with self.assertRaises(ValueError):h['combine_predictions']([[1,1,1]],[.5])
        with self.assertRaises(ValueError):h['combine_predictions']([[1,0,0]],[float('nan')])
        frame=pd.DataFrame([dict(dataset='MILK10k',image_id='x',image_path='x.jpg',image_hash='x',class_label='SCC',label_index=2,split='validation')])
        with self.assertRaises(ValueError):h['validate_manifest'](frame,'train','training')

    @unittest.skipUnless(importlib.util.find_spec('tensorflow'),'TensorFlow is installed in CI; unavailable in this local CPU runtime')
    def test_specialist_training_cannot_mutate_source_backbone(self):
        import tensorflow as tf
        h=helpers(tf)
        tf.keras.backend.clear_session();tf.keras.utils.set_random_seed(42)
        inp=tf.keras.Input(shape=(8,8,3));features=tf.keras.layers.Conv2D(4,3,padding='same',activation='relu')(inp)
        base=tf.keras.Model(inp,features,name='resnet50')
        image=tf.keras.Input(shape=(8,8,3));x=base(image);x=tf.keras.layers.GlobalAveragePooling2D()(x)
        source=tf.keras.Model(image,tf.keras.layers.Dense(3,activation='softmax')(x))
        reference=[a.copy() for a in source.get_weights()]
        specialist,clone=h['build_specialist'](source)
        self.assertIsNot(clone,base)
        for a,b in zip(base.get_weights(),clone.get_weights()):np.testing.assert_allclose(a,b)
        clone.trainable=True
        specialist.compile(optimizer=tf.keras.optimizers.SGD(.01),loss='binary_crossentropy')
        specialist.train_on_batch(np.ones((2,8,8,3),dtype='float32'),np.array([[0.],[1.]],dtype='float32'))
        for a,b in zip(reference,source.get_weights()):np.testing.assert_array_equal(a,b)
        self.assertEqual(specialist.output_shape[-1],1)
        tf.keras.backend.clear_session()

if __name__=='__main__':unittest.main()
