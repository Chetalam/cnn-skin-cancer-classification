"""Decision-boundary guards: recover sensitivity without hiding false positives."""
import ast
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

NOTEBOOK=Path(__file__).resolve().parents[1]/'notebooks'/'14_scc_decision_boundary_check.ipynb'

def helpers():
    scope={'np':np,'pd':pd,'CLASS_NAMES':['BCC','Melanoma','SCC']}
    for cell in json.loads(NOTEBOOK.read_text())['cells']:
        if cell['cell_type']!='code':continue
        tree=ast.parse(''.join(cell['source']))
        for node in tree.body:
            if isinstance(node,ast.FunctionDef) and node.name in {'apply_policy','decision_metrics','targets_met'}:
                exec(compile(ast.Module(body=[node],type_ignores=[]),'<helper>','exec'),scope)
    return scope

class SCCBoundaryTests(unittest.TestCase):
    def test_weighting_can_recover_scc_without_mutating_scores(self):
        h=helpers();scores=np.array([[.95,.04,.01],[.02,.97,.01],[.55,.05,.40]])
        copy=scores.copy()
        np.testing.assert_array_equal(h['apply_policy'](scores,1,1),[0,1,0])
        pred=h['apply_policy'](scores,1,1.5)
        np.testing.assert_array_equal(pred,[0,1,2])
        np.testing.assert_array_equal(scores,copy)
        metrics,_,_=h['decision_metrics'](np.array([0,1,2]),pred)
        self.assertTrue(h['targets_met'](metrics))

    def test_calling_everything_scc_does_not_pass(self):
        h=helpers();metrics,_,_=h['decision_metrics'](np.array([0,1,2]),np.array([2,2,2]))
        self.assertEqual(metrics['SCC_recall'],1)
        self.assertFalse(h['targets_met'](metrics))

    def test_macro_target_is_strict_and_other_class_recall_matters(self):
        h=helpers();m=dict(accuracy=.9,macro_f1=.80,BCC_recall=.9,Melanoma_recall=.9,SCC_recall=.9)
        self.assertFalse(h['targets_met'](m))
        m['macro_f1']=.81;m['Melanoma_recall']=.79
        self.assertFalse(h['targets_met'](m))

    def test_invalid_scores_and_weights_are_rejected(self):
        h=helpers()
        for values,mw,sw in [(np.array([[1.,1.,1.]]),1,1),(np.array([[.2,.3,.5]]),1,0),(np.array([[.2,np.nan,.5]]),1,1)]:
            with self.assertRaises(ValueError):h['apply_policy'](values,mw,sw)

if __name__=='__main__':unittest.main()
