"""One Reviews screen preserves editing, prediction provenance and retained data."""
import importlib.util
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

    def test_dashboard_has_actions_without_recent_review_table(self):
        app=self.page('1_Dashboard.py')
        self.assertFalse(any(item.value=='Your recent reviews' for item in app.subheader))
        self.assertEqual(len(app.dataframe),0)
        labels=[item.proto.label for item in app.get('page_link')]
        self.assertIn('Open Analyse Image',labels);self.assertIn('View Reviews',labels)
        self.assertEqual(len(app.metric),3)


if __name__=='__main__':unittest.main()
