import sqlite3
from test_prediction_analytics import PredictionAnalytics, db

class ReviewArchiving(PredictionAnalytics):
    def test_archive_restore_preserves_complete_prediction(self):
        image=self.review(self.worker,'archive')
        db.record_prediction(self.worker,image,'a'*64,self.result)
        before=db.prediction_detail(self.worker,image)
        thumbnail=db.get_thumbnail(self.worker,image)
        self.assertEqual(db.archive_review(self.outside,image),0)
        self.assertEqual(db.archive_review(self.worker,image),1)
        self.assertEqual(db.archive_review(self.worker,image),0)
        self.assertEqual(db.history(self.worker),[])
        self.assertIsNotNone(db.history(self.worker,view='archived')[0]['archived_at'])
        self.assertEqual(db.prediction_detail(self.worker,image),before)
        self.assertEqual(db.get_thumbnail(self.worker,image),thumbnail)
        self.assertEqual(db.analytics(self.admin)['archived'],1)
        with self.assertRaises(ValueError):db.update_review(self.worker,image,'changed while archived')
        with self.assertRaises(ValueError):db.record_prediction(self.worker,image,'a'*64,self.result)
        self.assertEqual(db.restore_review(self.outside,image),0)
        self.assertEqual(db.restore_review(self.worker,image),1)
        self.assertEqual(len(db.history(self.worker)),1)
        self.assertEqual(db.prediction_detail(self.worker,image),before)
        with db.connect() as c:
            actions=[r[0] for r in c.execute("SELECT action FROM audit_events WHERE action IN ('image_review_archived','image_review_restored')")]
        self.assertEqual(actions,['image_review_archived','image_review_restored'])

    def test_sql_hard_delete_is_blocked(self):
        image=self.review(self.worker,'retained')
        with self.assertRaises(sqlite3.IntegrityError):
            with db.connect() as c:c.execute('DELETE FROM skin_lesion_images WHERE id=?',(image,))
        self.assertEqual(len(db.history(self.worker)),1)

    def test_additive_migration_preserves_existing_rows_and_makes_backup(self):
        image=self.review(self.worker,'migration')
        db.record_prediction(self.worker,image,'a'*64,self.result)
        before=db.prediction_detail(self.worker,image)
        with db.connect() as c:
            c.execute('ALTER TABLE skin_lesion_images DROP COLUMN archived_at')
            c.execute('DELETE FROM schema_version WHERE version=7')
        db.initialize()
        self.assertEqual(db.prediction_detail(self.worker,image),before)
        self.assertIsNone(db.history(self.worker)[0]['archived_at'])
        self.assertEqual(len(list(db.DB_PATH.parent.glob('backups/*.before_review_archiving_*.db'))),1)
        db.initialize()
        self.assertEqual(len(list(db.DB_PATH.parent.glob('backups/*.before_review_archiving_*.db'))),1)
        with db.connect() as c:
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
