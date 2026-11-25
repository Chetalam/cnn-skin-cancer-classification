"""One Reviews screen preserves editing, prediction provenance and retained data."""
import importlib.util
import io
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

APP=Path(__file__).resolve().parents[1]/'app'
sys.path.insert(0,str(APP))


@unittest.skipUnless(importlib.util.find_spec('streamlit'),'Streamlit is not installed')
class UnifiedReviews(unittest.TestCase):
    def setUp(self):
        import db
        self.db=db
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        old=db.DB_PATH;db.DB_PATH=Path(self.temp.name)/'fixture.db';self.addCleanup(setattr,db,'DB_PATH',old)
        db.initialize()
        password='Private fixture passphrase 123'
        self.worker=db.register('Fixture Worker','worker@fixture.test',password,'Fixture centre')
        self.token=db.sign_in('worker@fixture.test',password)
        self.image=db.save_review(self.worker,'fixture-request','Original case','fixture.png',Image.new('RGB',(20,20)),'a'*64)
        db.record_prediction(self.worker,self.image,'a'*64,dict(scores={'BCC':.1,'Melanoma':.2,'SCC':.7},model_name='Fixture CNN',run_id='historical_fixture',model_sha256='b'*64,artifact_path='fixture.keras',preprocessing='fixture'))
        from streamlit.runtime.pages_manager import PagesManager
        old_mode=PagesManager.uses_pages_directory
        PagesManager.uses_pages_directory=None
        self.addCleanup(setattr,PagesManager,'uses_pages_directory',old_mode)

    def page(self,name):
        from streamlit.testing.v1 import AppTest
        page=AppTest.from_file(str(APP/'streamlit_app.py'))
        page.session_state['auth_token']=self.token
        page.run(timeout=25)
        page.switch_page('pages/'+name).run(timeout=25)
        self.assertEqual([e.message for e in page.exception],[])
        return page

    def test_reviews_edit_archive_restore_and_referral(self):
        from referral import checklist_text
        app=self.page('3_History.py')
        self.assertEqual(app.title[0].value,'Reviews')
        labels=[item.proto.label for item in app.get('page_link')]
        self.assertEqual(labels.count('Reviews'),1)
        self.assertNotIn('History',labels);self.assertNotIn('Review Records',labels)
        field=next(field for field in app.text_input if field.label=='Case reference')
        field.set_value('Updated case')
        next(button for button in app.button if button.label=='Update case reference').click().run(timeout=25)
        self.assertEqual([e.message for e in app.exception],[])
        self.assertEqual(self.db.history(self.worker)[0]['case_reference'],'Updated case')
        text=checklist_text(self.db.prediction_detail(self.worker,self.image))
        self.assertIn('Updated case',text);self.assertIn('historical_fixture',text)
        app.checkbox(key=f'history_{self.image}_confirm').check().run(timeout=25)
        app.button(key=f'history_{self.image}_archive').click().run(timeout=25)
        self.assertEqual(self.db.history(self.worker),[])
        app.radio(key='history_view').set_value('archived').run(timeout=25)
        self.assertFalse(any(field.label=='Case reference' for field in app.text_input))
        self.assertEqual(len(app.get('download_button')),2)
        app.button(key=f'history_{self.image}_restore').click().run(timeout=25)
        self.assertEqual(len(self.db.history(self.worker)),1)
        with self.db.connect() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM prediction_results').fetchone()[0],1)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM prediction_scores').fetchone()[0],3)
        self.assertEqual([e.message for e in app.exception],[])

    def test_old_review_uses_its_stored_preview_without_upload(self):
        from images import validate_image

        original = io.BytesIO()
        Image.new('RGB', (960, 1280), 'red').save(original, format='PNG')
        raw = original.getvalue()
        image, digest = validate_image(raw)
        review_id = self.db.save_review(self.worker, 'pending', 'Case 2', 'original.png', image, digest)
        result = dict(scores={'BCC': .6, 'Melanoma': .3, 'SCC': .1}, model_name='Fixture CNN',
                      run_id='resume', model_sha256='b' * 64, artifact_path='fixture.keras', preprocessing='fixture')
        preview = self.db.get_thumbnail(self.worker, review_id)
        original_digest = digest
        _, digest = validate_image(preview)
        self.assertNotEqual(digest, original_digest)
        with self.assertRaises(ValueError):
            self.db.record_prediction(self.worker, review_id, original_digest, result, from_preview=True)
        with patch('inference.predict_image') as predict:
            app = self.page('3_History.py')
            app.radio(key='review_status_view').set_value('Awaiting prediction').run()
            self.assertFalse(app.get('file_uploader'))
            run_key = f'resume_predict_{review_id}'
            self.assertTrue(app.button(key=run_key).disabled)
            app.radio(key=f'lesion_visibility_resume_{review_id}_{digest}').set_value('Yes').run()
            self.assertTrue(app.button(key=run_key).disabled)
            app.checkbox(key=f'lesion_limitation_ack_resume_{review_id}_{digest}').check().run()
            predict.side_effect = ValueError('Model unavailable')
            app.button(key=run_key).click().run()
            self.assertEqual(self.db.prediction_detail(self.worker, review_id)['status'], 'awaiting_model')
            predict.side_effect = None
            predict.return_value = result
            app.button(key=run_key).click().run()
            self.assertEqual([e.message for e in app.exception], [])
            predict.assert_called_with(preview, lesion_confirmed=True, limitation_acknowledged=True)
            self.assertEqual(app.radio(key='review_status_view').value, 'Completed predictions')
            self.assertEqual(app.selectbox(key='history_selection_active_Completed predictions').value, review_id)
            detail = self.db.prediction_detail(self.worker, review_id)
            self.assertEqual((detail['status'], detail['case_reference']), ('predicted', 'Case 2'))
            self.assertEqual(detail['preview_sha256'], digest)
            self.assertEqual(detail['image_sha256'], original_digest)
            from explainability import prediction_image_digest
            self.assertEqual(prediction_image_digest(detail), digest)
            self.assertFalse(app.get('file_uploader'))
            self.assertEqual(len(self.db.history(self.worker)), 2)

    def test_finish_new_review_after_reopening_without_upload(self):
        from images import validate_image

        photo = io.BytesIO()
        photo.name = 'lesion.png'
        Image.new('RGB', (450, 300), 'red').save(photo, format='PNG')
        raw = photo.getvalue()
        _, digest = validate_image(raw)
        with patch('streamlit.file_uploader', return_value=photo):
            form = self.page('2_Analyse_Image.py')
            consent = next(c for c in form.checkbox if c.label.startswith('Save this image'))
            consent.check().run()
            next(b for b in form.button if b.label == 'Save without prediction').click().run()
            self.assertFalse(form.exception)
        review_id = self.db.history(self.worker)[0]['id']
        self.assertEqual(self.db.get_pending_original(self.worker, review_id), raw)

        outsider = self.db.register('Other Worker', 'other@fixture.test', 'Another password 123', 'Fixture centre')
        with self.assertRaises(ValueError):
            self.db.get_pending_original(outsider, review_id)
        self.db.archive_review(self.worker, review_id)
        with self.assertRaises(ValueError):
            self.db.get_pending_original(self.worker, review_id)
        self.db.restore_review(self.worker, review_id)

        app = self.page('3_History.py')
        app.radio(key='review_status_view').set_value('Awaiting prediction').run()
        self.assertFalse(app.get('file_uploader'))
        button = f'resume_predict_{review_id}'
        self.assertTrue(app.button(key=button).disabled)
        app.radio(key=f'lesion_visibility_resume_{review_id}_{digest}').set_value('Yes').run()
        app.checkbox(key=f'lesion_limitation_ack_resume_{review_id}_{digest}').check().run()
        with patch('inference.predict_image') as predict:
            predict.side_effect = ValueError('Model unavailable')
            app.button(key=button).click().run()
            self.assertEqual(self.db.get_pending_original(self.worker, review_id), raw)
            predict.side_effect = None
            predict.return_value = dict(scores={'BCC': .6, 'Melanoma': .3, 'SCC': .1}, model_name='Fixture CNN',
                                        run_id='resume', model_sha256='b'*64, artifact_path='fixture.keras', preprocessing='fixture')
            app.button(key=button).click().run()
            self.assertFalse(app.exception)
            predict.assert_called_with(raw, lesion_confirmed=True, limitation_acknowledged=True)
        self.assertEqual(self.db.prediction_detail(self.worker, review_id)['status'], 'predicted')
        self.assertEqual(len(self.db.history(self.worker)), 2)
        with self.db.connect() as conn:
            self.assertIsNone(conn.execute('SELECT pending_original FROM skin_lesion_images WHERE id=?', (review_id,)).fetchone()[0])

    def test_preview_only_database_upgrades_in_place(self):
        old = self.db.save_review(self.worker, 'old', '', 'old.png', Image.new('RGB', (20, 20)), 'c'*64)
        with self.db.connect() as conn:
            conn.execute('ALTER TABLE skin_lesion_images DROP COLUMN pending_original')
            conn.execute('DELETE FROM schema_version WHERE version=8')
        self.db.initialize()
        self.db.initialize()
        self.assertIsNone(self.db.get_pending_original(self.worker, old))
        self.assertEqual(self.db.prediction_detail(self.worker, old)['status'], 'awaiting_model')
        self.assertEqual(self.db.prediction_detail(self.worker, self.image)['status'], 'predicted')

    def test_dashboard_has_actions_without_recent_review_table(self):
        app=self.page('1_Dashboard.py')
        self.assertFalse(any(item.value=='Your recent reviews' for item in app.subheader))
        self.assertEqual(len(app.dataframe),0)
        labels=[item.proto.label for item in app.get('page_link')]
        self.assertIn('Open Analyse Image',labels);self.assertIn('View Reviews',labels)
        self.assertEqual(len(app.metric),3)


if __name__=='__main__':unittest.main()
