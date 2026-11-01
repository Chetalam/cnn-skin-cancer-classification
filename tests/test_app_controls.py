"""Account and ownership checks against isolated SQLite databases."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

from PIL import Image

APP = Path(__file__).resolve().parents[1] / "app"
spec = importlib.util.spec_from_file_location("app_db_under_test", APP / "db.py")
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)


class AccountControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.previous_path = db.DB_PATH
        db.DB_PATH = Path(self.directory.name) / "application.db"
        db.initialize()
        self.password = "Private test passphrase 123"
        self.admin = db.register("Admin One", "admin@example.com", self.password,
                                 "Clinic A", requested_role="system_administrator")
        self.worker = db.register("Worker One", "worker@example.com", self.password, "Clinic A")
        self.outsider = db.register("Other Worker", "other@example.com", self.password, "Clinic B")

    def tearDown(self):
        db.DB_PATH = self.previous_path
        self.directory.cleanup()

    def review(self):
        return db.save_review(self.worker, "request-1", "anonymous-case", "sample.png",
                              Image.new("RGB", (24, 24)), "a" * 64)

    def test_hashes_and_foreign_keys(self):
        with db.connect() as connection:
            encoded = connection.execute("SELECT password_hash FROM users WHERE id=?", (self.worker,)).fetchone()[0]
            self.assertNotEqual(encoded, self.password)
            self.assertTrue(db.verify_password(self.password, encoded))
            self.assertFalse(db.verify_password("incorrect", encoded))
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertFalse(connection.execute("PRAGMA foreign_key_check").fetchall())

    def test_review_ownership_and_cascade_delete(self):
        image_id = self.review()
        self.assertEqual(db.history(self.outsider), [])
        self.assertIsNone(db.get_thumbnail(self.outsider, image_id))
        self.assertEqual(db.delete_review(self.outsider, image_id), 0)
        with self.assertRaises(ValueError):
            db.update_review(self.outsider, image_id, "wrong-owner")
        db.update_review(self.worker, image_id, "updated")
        self.assertEqual(db.history(self.worker)[0]["case_reference"], "updated")
        self.assertEqual(db.delete_review(self.worker, image_id), 1)
        with db.connect() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM prediction_results").fetchone()[0], 0)

    def test_administrator_cannot_use_review_functions(self):
        image_id = self.review()
        for action in [lambda: db.history(self.admin),
                       lambda: db.get_thumbnail(self.admin, image_id),
                       lambda: db.update_review(self.admin, image_id, "change"),
                       lambda: db.delete_review(self.admin, image_id),
                       lambda: db.save_review(self.admin, "admin", "case", "image.png", Image.new("RGB", (4, 4)), "b" * 64)]:
            with self.assertRaises(ValueError):
                action()
        with self.assertRaises(ValueError):
            db.list_accounts_for_review(self.worker)

    def test_deactivation_preserves_reviews_and_revokes_sessions(self):
        image_id = self.review()
        first = db.sign_in("worker@example.com", self.password)
        second = db.sign_in("worker@example.com", self.password)
        db.deactivate_profile(first, self.password)
        self.assertIsNone(db.session_user(first))
        self.assertIsNone(db.session_user(second))
        with self.assertRaises(ValueError):
            db.sign_in("worker@example.com", self.password)
        with db.connect() as connection:
            self.assertEqual(connection.execute("SELECT user_id FROM skin_lesion_images WHERE id=?", (image_id,)).fetchone()[0], self.worker)
        db.review_account(self.admin, self.worker, "active")
        self.assertEqual(len(db.history(self.worker)), 1)

    def test_last_administrator_and_centre_boundaries(self):
        token = db.sign_in("admin@example.com", self.password)
        with self.assertRaises(ValueError):
            db.deactivate_profile(token, self.password)
        with self.assertRaises(ValueError):
            db.review_account(self.admin, self.outsider, "suspended")
        self.assertNotIn(self.outsider, [row["id"] for row in db.list_accounts_for_review(self.admin)])

    def test_migration_removes_approval_columns_without_losing_relationships(self):
        # Seed the prior users shape while retaining records in related tables.
        image_id = self.review()
        with db.connect() as connection:
            original_hash = connection.execute("SELECT password_hash FROM users WHERE id=?", (self.worker,)).fetchone()[0]
            connection.execute("ALTER TABLE users ADD COLUMN approved_at INTEGER")
            connection.execute("ALTER TABLE users ADD COLUMN approved_by INTEGER REFERENCES users(id)")
            connection.execute("DELETE FROM schema_version WHERE version=6")
        db.initialize()
        with db.connect() as connection:
            names = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
            self.assertFalse({"approved_at", "approved_by"} & names)
            self.assertEqual(connection.execute("SELECT password_hash FROM users WHERE id=?", (self.worker,)).fetchone()[0], original_hash)
            self.assertEqual(connection.execute("SELECT user_id FROM skin_lesion_images WHERE id=?", (image_id,)).fetchone()[0], self.worker)
            self.assertFalse(connection.execute("PRAGMA foreign_key_check").fetchall())
        self.assertTrue(list(Path(self.directory.name).glob("*.before_profile_update_*.db")))


if __name__ == "__main__":
    unittest.main()
