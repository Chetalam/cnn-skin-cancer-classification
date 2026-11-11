"""Administrator information uses normal tables and distinct page responsibilities."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))


@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit is not installed')
class AdminPageLayout(unittest.TestCase):
    def setUp(self):
        import db
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        old = db.DB_PATH
        db.DB_PATH = Path(self.temp.name) / 'fixture.db'
        self.addCleanup(setattr, db, 'DB_PATH', old)
        db.initialize()
        password = 'Private fixture passphrase 123'
        db.register('Fixture Admin', 'admin@fixture.test', password,
                    'Fixture centre', requested_role='system_administrator')
        db.register('Fixture Worker', 'worker@fixture.test', password,
                    'Fixture centre')
        self.token = db.sign_in('admin@fixture.test', password)
        from streamlit.runtime.pages_manager import PagesManager
        old_mode = PagesManager.uses_pages_directory
        PagesManager.uses_pages_directory = None
        self.addCleanup(setattr, PagesManager, 'uses_pages_directory', old_mode)

    def page(self, name):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(APP / 'streamlit_app.py'))
        app.session_state['auth_token'] = self.token
        app.run(timeout=25)
        app.switch_page('pages/' + name).run(timeout=25)
        self.assertEqual([e.message for e in app.exception], [])
        return app

    def test_admin_tables_do_not_use_scrollable_grids(self):
        for name in ['1_Dashboard.py', '7_User_Management.py']:
            with self.subTest(page=name):
                app = self.page(name)
                self.assertEqual(len(app.dataframe), 0)
                self.assertGreater(len(app.table), 0)

    def test_dataset_import_and_database_checks_have_distinct_homes(self):
        dataset = self.page('5_Dataset_Status.py')
        self.assertEqual(dataset.title[0].value, 'Dataset Status')
        self.assertEqual(len(dataset.get('file_uploader')), 1)
        self.assertEqual(len(dataset.tabs), 0)
        self.assertFalse(any(s.value == 'Current database checks' for s in dataset.subheader))
        guide = self.page('9_Database_Guide.py')
        self.assertEqual(len(guide.tabs), 3)
        self.assertEqual(len(guide.dataframe), 0)
        self.assertEqual(len(guide.get('file_uploader')), 0)
        self.assertTrue(any(s.value == 'Current database checks' for s in guide.subheader))


if __name__ == '__main__':
    unittest.main()
