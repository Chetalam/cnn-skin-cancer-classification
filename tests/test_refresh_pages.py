"""Smoke-test role navigation and bilingual pages against a disposable database."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from streamlit.testing.v1 import AppTest
import db
from branding import PROJECT_NAME
ROOT=Path(__file__).resolve().parents[1]

class RefreshPages(unittest.TestCase):
    def setUp(self):
        from streamlit.runtime.pages_manager import PagesManager
        old_mode=PagesManager.uses_pages_directory
        PagesManager.uses_pages_directory=None
        self.addCleanup(setattr,PagesManager,"uses_pages_directory",old_mode)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        old=db.DB_PATH;db.DB_PATH=Path(self.tmp.name)/'app.db'
        self.addCleanup(setattr,db,'DB_PATH',old)
        db.initialize()
        self.password='Test passphrase only 2026'
        for role,email in [('healthcare_worker','worker@example.test'),('system_administrator','admin@example.test')]:
            db.register('Test user',email,self.password,'QA Clinic',requested_role=role)

    def test_login_and_language_persist_across_pages(self):
        at=AppTest.from_file(str(ROOT/'app/streamlit_app.py')).run()
        self.assertFalse(at.exception)
        self.assertTrue(any(PROJECT_NAME in m.value for m in at.markdown))
        at.session_state['app_language']='sw'
        at.run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Kagua picha' in m.value for m in at.markdown))

    def test_worker_and_admin_pages(self):
        for email,pages in [('worker@example.test',['1_Dashboard.py','2_Analyse_Image.py','3_History.py','10_Analytics.py','4_Account.py']),('admin@example.test',['1_Dashboard.py','7_User_Management.py','5_Dataset_Status.py','9_Database_Guide.py','10_Analytics.py'])]:
            token=db.sign_in(email,self.password)
            for page in pages:
                with self.subTest(page=page,email=email):
                    at=AppTest.from_file(str(ROOT/'app/streamlit_app.py')).run()
                    at.session_state['auth_token']=token
                    at.session_state['app_language']='sw'
                    at.switch_page('pages/'+page).run(timeout=20)
                    self.assertFalse(at.exception)
                    self.assertEqual(at.session_state['app_language'],'sw')
                    if page=='2_Analyse_Image.py':
                        buttons=[b for b in at.button if b.label in ['Analyse and save','Changanua na uhifadhi']]
                        self.assertTrue(buttons)
                        self.assertTrue(buttons[0].disabled)
