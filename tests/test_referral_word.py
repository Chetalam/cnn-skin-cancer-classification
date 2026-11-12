"""Word reports preserve saved results and distinguish education from explanation."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from docx import Document
from referral_document import checklist_docx
from classification_info import CLASS_INFO, GENERAL_ONLY, LIMIT, CLOSED_SET, interpretation


class ReferralWord(unittest.TestCase):
    def fixture(self, label='BCC'):
        scores = dict.fromkeys(CLASS_INFO, .1)
        scores[label] = .8
        return dict(image_id=6, status='predicted', cancer_class=label, confidence=.8,
                    scores=scores, created_at=1730000000, case_reference='Example\ncase',
                    model_name='ResNet50 / saved_run / historical_sha')

    def test_each_class_exports_complete_saved_prediction_and_spaced_handover(self):
        for label in CLASS_INFO:
            with self.subTest(label=label), patch('referral_document.t', side_effect=lambda x:x), patch('classification_info.t', side_effect=lambda x:x):
                document = Document(BytesIO(checklist_docx(self.fixture(label))))
                paragraphs = '\n'.join(p.text for p in document.paragraphs)
                table = '\n'.join(c.text for row in document.tables[0].rows for c in row.cells)
                for required in ['Review ID: 6', 'Case reference: Example case', label,
                                 'saved_run', 'historical_sha', GENERAL_ONLY, LIMIT, CLOSED_SET,
                                 'SCC limitation', 'Clinical findings and reason for referral']:
                    self.assertIn(required, paragraphs)
                for required in CLASS_INFO:
                    self.assertIn(required, table)
                self.assertIn('80.0%', table)
                self.assertEqual(document.styles['Normal'].paragraph_format.line_spacing,1.15)
                self.assertEqual(document.paragraphs[0].style.name,'Title')

    def test_incomplete_and_inconsistent_predictions_cannot_export(self):
        for changes in [dict(status='awaiting_model'), dict(scores={'BCC':.8}), dict(confidence=float('nan')),
                        dict(confidence=.2), dict(cancer_class='SCC', confidence=.1)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                checklist_docx({**self.fixture(), **changes})

    def test_tied_scores_do_not_claim_unique_winner(self):
        value=self.fixture();value.update(confidence=.45,scores={'BCC':.45,'Melanoma':.45,'SCC':.1})
        with patch('classification_info.t',side_effect=lambda x:x):
            self.assertIn('tied for the highest',interpretation(value))

    def test_kiswahili_description_and_word_download(self):
        import streamlit as st
        from streamlit.testing.v1 import AppTest
        script = '''
import streamlit as st
from referral import show_referral_guidance
show_referral_guidance('fixture',dict(image_id=6,status='predicted',cancer_class='BCC',confidence=.8,scores={'BCC':.8,'Melanoma':.1,'SCC':.1},created_at=1730000000,case_reference='Fixture',model_name='Saved model'))
'''
        app=AppTest.from_string(script)
        app.session_state['app_language']='sw'
        app.run(timeout=25)
        self.assertEqual([e.message for e in app.exception],[])
        self.assertTrue(any(s.value=='Kuhusu aina inayoshukiwa' for s in app.subheader))
        self.assertEqual(len(app.get('download_button')),1)
        self.assertIn('Word',app.get('download_button')[0].proto.label)


if __name__=='__main__':unittest.main()
