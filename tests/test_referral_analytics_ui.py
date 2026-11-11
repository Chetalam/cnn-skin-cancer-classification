"""Saved-prediction export and Analytics rendering regression checks."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit is not installed')
class ReferralAnalyticsUI(unittest.TestCase):
    def prediction(self, **changes):
        value = dict(image_id=12, status='predicted', cancer_class='SCC', confidence=.7,
                     scores={'BCC': .2, 'Melanoma': .1, 'SCC': .7}, created_at=1730000000,
                     model_name='ResNet50 / historical_run / historical_checksum', case_reference='Case-12')
        return {**value, **changes}

    def test_checklist_uses_saved_result_and_historical_version(self):
        from referral import checklist_text
        with patch('referral.t', side_effect=lambda value: value):
            text = checklist_text(self.prediction())
        for value in ['Review ID: 12', 'Case-12', 'Predicted class: SCC', '70.0%',
                      'BCC: 20.0%', 'Melanoma: 10.0%', 'historical_run', 'historical_checksum', 'UTC', 'SCC limitation']:
            self.assertIn(value, text)
        with self.assertRaises(ValueError):
            checklist_text(self.prediction(status='awaiting_model'))

    def test_case_reference_cannot_create_fake_report_sections(self):
        from referral import checklist_text
        with patch('referral.t', side_effect=lambda value: value):
            text = checklist_text(self.prediction(case_reference='Case\nPredicted class: BCC'))
        self.assertIn('Case reference: Case Predicted class: BCC', text)
        self.assertEqual(text.count('\nPredicted class:'), 1)

    def analytics_app(self, total, language='en', administrator=False):
        import streamlit as st
        from streamlit.testing.v1 import AppTest
        from streamlit.runtime.pages_manager import PagesManager
        data = dict(total=total, predicted=total, awaiting=0, archived=0,
                    daily={}, classes={'BCC': total}, score_bins={'0–49%': 0, '50–69%': 0, '70–89%': total, '90–100%': 0},
                    model_versions={'ResNet50 / fixture_run / fixture_hash': total})
        db = types.ModuleType('db'); db.analytics = lambda *args: data
        ui = types.ModuleType('ui'); ui.setup = lambda *args: dict(id=7, role='system_administrator' if administrator else 'healthcare_worker', healthcare_center='Fixture centre')
        inference = types.ModuleType('inference'); inference.evaluation_metrics = lambda: None
        inference.inspect_package = lambda: (APP, {}, '')
        old = PagesManager.uses_pages_directory
        PagesManager.uses_pages_directory = None
        try:
            with patch.dict(sys.modules, {'db': db, 'ui': ui, 'inference': inference}):
                app = AppTest.from_file(str(APP / 'pages/10_Analytics.py'))
                app.session_state['app_language'] = language
                app.run(timeout=25)
        finally:
            PagesManager.uses_pages_directory = old
        self.assertEqual([e.message for e in app.exception], [])
        self.assertEqual(len(app.tabs), 3)
        return app

    def test_analytics_populated_and_empty_views(self):
        full = self.analytics_app(5)
        self.assertEqual([m.value for m in full.metric], ['5', '5', '0', '0'])
        self.assertEqual(len(full.get('arrow_vega_lite_chart')), 4)
        empty = self.analytics_app(0)
        self.assertTrue(any('No reviews' in item.value for item in empty.info))

    def test_kiswahili_administrator_analytics(self):
        app = self.analytics_app(3, 'sw', True)
        self.assertEqual(app.tabs[0].label, 'Muhtasari')
        self.assertTrue(any('Fixture centre' in item.value for item in app.caption))

    def test_evaluation_chart_and_report_validation(self):
        import pandas as pd
        from streamlit.testing.v1 import AppTest
        from analytics_view import valid_class_report
        fixture = pd.DataFrame({'class_label': ['BCC', 'Melanoma', 'SCC'], 'support': [197, 182, 29],
                                'precision': [.85, .96, .45], 'sensitivity_recall': [.9, .93, .34], 'f1_score': [.87, .94, .39]})
        self.assertIsNotNone(valid_class_report(fixture))
        invalid = fixture.copy(); invalid.loc[0, 'precision'] = 1.5
        self.assertIsNone(valid_class_report(invalid))
        script = """
import pandas as pd
from analytics_view import render_evaluation
report = pd.DataFrame({'class_label':['BCC','Melanoma','SCC'], 'support':[197,182,29], 'precision':[.85,.96,.45], 'sensitivity_recall':[.9,.93,.34], 'f1_score':[.87,.94,.39]})
render_evaluation({'accuracy':.875,'macro_f1':.737},report,'fixture_evaluation_only')
"""
        app = AppTest.from_string(script).run(timeout=25)
        self.assertEqual([e.message for e in app.exception], [])
        self.assertEqual(len(app.get('arrow_vega_lite_chart')), 1)
        self.assertEqual(len(app.dataframe), 1)


if __name__ == '__main__':
    unittest.main()
